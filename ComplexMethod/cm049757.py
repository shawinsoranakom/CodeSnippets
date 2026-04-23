def _redirect_to_record(cls, model, res_id, access_token=None, **kwargs):
        # access_token and kwargs are used in the portal controller override for the Send by email or Share Link
        # to give access to the record to a recipient that has normally no access.
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        cids = []

        # no model / res_id, meaning no possible record -> redirect to login
        if not model or not res_id or model not in request.env:
            return cls._redirect_to_generic_fallback(
                model, res_id, access_token=access_token, **kwargs,
            )

        # find the access action using sudo to have the details about the access link
        RecordModel = request.env[model]
        record_sudo = RecordModel.sudo().browse(res_id).exists()
        if not record_sudo:
            # record does not seem to exist -> redirect to login
            return cls._redirect_to_generic_fallback(
                model, res_id, access_token=access_token, **kwargs,
            )

        suggested_company = record_sudo._get_redirect_suggested_company()
        # the record has a window redirection: check access rights
        if uid is not None:
            if not RecordModel.with_user(uid).has_access('read'):
                return cls._redirect_to_generic_fallback(
                    model, res_id, access_token=access_token, **kwargs,
                )
            try:
                # We need here to extend the "allowed_company_ids" to allow a redirection
                # to any record that the user can access, regardless of currently visible
                # records based on the "currently allowed companies".
                cids_str = request.cookies.get('cids', str(user.company_id.id))
                cids = [int(cid) for cid in cids_str.split('-')]
                try:
                    record_sudo.with_user(uid).with_context(allowed_company_ids=cids).check_access('read')
                except AccessError:
                    # In case the allowed_company_ids from the cookies (i.e. the last user configuration
                    # on their browser) is not sufficient to avoid an ir.rule access error, try to following
                    # heuristic:
                    # - Guess the supposed necessary company to access the record via the method
                    #   _get_redirect_suggested_company
                    #   - If no company, then redirect to the messaging
                    #   - Merge the suggested company with the companies on the cookie
                    # - Make a new access test if it succeeds, redirect to the record. Otherwise,
                    #   redirect to the messaging.
                    if not suggested_company:
                        raise AccessError(_("There is no candidate company that has read access to the record."))
                    cids = cids + [suggested_company.id]
                    record_sudo.with_user(uid).with_context(allowed_company_ids=cids).check_access('read')
                    request.future_response.set_cookie('cids', '-'.join([str(cid) for cid in cids]))
            except AccessError:
                return cls._redirect_to_generic_fallback(
                    model, res_id, access_token=access_token, **kwargs,
                )
            else:
                record_action = record_sudo._get_access_action(access_uid=uid)
        else:
            record_action = record_sudo._get_access_action()
            # we have an act_url (probably a portal link): we need to retry being logged to check access
            if record_action['type'] == 'ir.actions.act_url' and record_action.get('target_type') != 'public':
                return cls._redirect_to_login_with_mail_view(
                    model, res_id, access_token=access_token, **kwargs,
                )

        record_action.pop('target_type', None)
        # the record has an URL redirection: use it directly
        if record_action['type'] == 'ir.actions.act_url':
            url = record_action["url"]
            if highlight_message_id := kwargs.get("highlight_message_id"):
                parsed_url = urlparse(url)
                url = parsed_url._replace(query=urlencode(
                    parse_qsl(parsed_url.query) + [("highlight_message_id", highlight_message_id)]
                )).geturl()
            return request.redirect(url)
        # anything else than an act_window is not supported
        elif record_action['type'] != 'ir.actions.act_window':
            return cls._redirect_to_messaging()

        # backend act_window: when not logged, unless really readable as public,
        # user is going to be redirected to login -> keep mail/view as redirect
        # in that case. In case of readable record, we consider this might be
        # a customization and we do not change the behavior in stable
        if uid is None or request.env.user._is_public():
            has_access = record_sudo.with_user(request.env.user).has_access('read')
            if not has_access:
                return cls._redirect_to_login_with_mail_view(
                    model, res_id, access_token=access_token, **kwargs,
                )

        url_params = {}
        menu_id = request.env['ir.ui.menu']._get_best_backend_root_menu_id_for_model(model)
        if menu_id:
            url_params['menu_id'] = menu_id
        view_id = record_sudo.get_formview_id()
        if view_id:
            url_params['view_id'] = view_id
        if highlight_message_id := kwargs.get("highlight_message_id"):
            url_params["highlight_message_id"] = highlight_message_id
        if cids:
            request.future_response.set_cookie('cids', '-'.join([str(cid) for cid in cids]))

        # @see commit c63d14a0485a553b74a8457aee158384e9ae6d3f
        # @see router.js: heuristics to discrimate a model name from an action path
        # is the presence of dots, or the prefix m- for models
        model_in_url = model if "." in model else "m-" + model
        url = f'/odoo/{model_in_url}/{res_id}?{url_encode(url_params, sort=True)}'
        return request.redirect(url)
def _redirect_to_record(cls, model, res_id, access_token=None, **kwargs):
        """ If the current user doesn't have access to the document, but provided
        a valid access token, redirect them to the front-end view.
        If the partner_id and hash parameters are given, add those parameters to the redirect url
        to authentify the recipient in the chatter, if any.

        :param model: the model name of the record that will be visualized
        :param res_id: the id of the record
        :param access_token: token that gives access to the record
            bypassing the rights and rules restriction of the user.
        :param kwargs: Typically, it can receive a partner_id and a hash (sign_token).
            If so, those two parameters are used to authentify the recipient in the chatter, if any.
        :return:
        """
        # no model / res_id, meaning no possible record -> direct skip to super
        if not model or not res_id or model not in request.env:
            return super(MailController, cls)._redirect_to_record(model, res_id, access_token=access_token, **kwargs)

        if isinstance(request.env[model], request.env.registry['portal.mixin']):
            uid = request.session.uid or request.env.ref('base.public_user').id
            record_sudo = request.env[model].sudo().browse(res_id).exists()
            try:
                record_sudo.with_user(uid).check_access('read')
            except AccessError:
                if record_sudo.access_token and access_token and consteq(record_sudo.access_token, access_token):
                    record_action = record_sudo._get_access_action(force_website=True)
                    if record_action['type'] == 'ir.actions.act_url':
                        pid = kwargs.get('pid')
                        hash = kwargs.get('hash')
                        url = record_action['url']
                        if pid and hash:
                            url = urls.url_parse(url)
                            url_params = url.decode_query()
                            url_params.update([("pid", pid), ("hash", hash)])
                            url = url.replace(query=urls.url_encode(url_params, sort=True)).to_url()
                        return request.redirect(url)
        return super(MailController, cls)._redirect_to_record(model, res_id, access_token=access_token, **kwargs)
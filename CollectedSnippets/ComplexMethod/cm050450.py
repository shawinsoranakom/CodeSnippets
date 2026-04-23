def pos_web(self, config_id=False, from_backend=False, subpath=None, **k):
        """Open a pos session for the given config.

        The right pos session will be selected to open, if non is open yet a new session will be created.

        /pos/ui and /pos/web both can be used to access the POS. On the SaaS,
        /pos/ui uses HTTPS while /pos/web uses HTTP.

        :param debug: The debug mode to load the session in.
        :type debug: str.
        :param config_id: id of the config that has to be loaded.
        :type config_id: str.
        :returns: object -- The rendered pos session.
        """
        is_internal_user = request.env.user._is_internal()
        pos_config = False
        if not is_internal_user:
            return request.not_found()
        domain = [
                ('state', 'in', ['opening_control', 'opened']),
                ('user_id', '=', request.session.uid),
                ('rescue', '=', False)
                ]
        if config_id and request.env['pos.config'].sudo().browse(int(config_id)).exists():
            domain = Domain.AND([domain, [('config_id', '=', int(config_id))]])
            pos_config = request.env['pos.config'].sudo().browse(int(config_id))
        pos_session = request.env['pos.session'].sudo().search(domain, limit=1)

        # The same POS session can be opened by a different user => search without restricting to
        # current user. Note: the config must be explicitly given to avoid fallbacking on a random
        # session.
        if not pos_session and config_id:
            domain = [
                ('state', 'in', ['opening_control', 'opened']),
                ('rescue', '=', False),
                ('config_id', '=', int(config_id)),
            ]
            pos_session = request.env['pos.session'].sudo().search(domain, limit=1)

        if not pos_config or not pos_config.active or pos_config.has_active_session and not pos_session:
            return request.redirect('/odoo/action-point_of_sale.action_client_pos_menu')

        if not pos_config.has_active_session:
            # Acquire an row-level lock on the pos_config record to prevent race conditions
            # This prevents multiple concurrent processes from creating duplicate POS sessions
            request.env.cr.execute(
                "SELECT id FROM pos_config WHERE id = %s FOR UPDATE NOWAIT",
                (pos_config.id,)
            )
            pos_config.open_ui()
            pos_session = request.env['pos.session'].sudo().search(domain, limit=1)

        # The POS only works in one company, so we enforce the one of the session in the context
        company = pos_session.company_id
        session_info = request.env['ir.http'].session_info()
        session_info['user_context']['allowed_company_ids'] = company.ids
        session_info['user_companies'] = {'current_company': company.id, 'allowed_companies': {company.id: session_info['user_companies']['allowed_companies'][company.id]}}
        session_info['nomenclature_id'] = pos_session.company_id.nomenclature_id.id
        session_info['fallback_nomenclature_id'] = pos_session.config_id.fallback_nomenclature_id.id
        use_lna = bool(pos_session.env["ir.config_parameter"].get_param("point_of_sale.use_lna"))
        context = {
            'from_backend': 1 if from_backend else 0,
            'use_pos_fake_tours': True if k.get('tours', False) else False,
            'session_info': session_info,
            'pos_session_id': pos_session.id,
            'pos_config_id': pos_session.config_id.id,
            'access_token': pos_session.config_id.access_token,
            'last_data_change': pos_session.config_id.last_data_change.strftime("%Y-%m-%d %H:%M:%S"),
            'urls_to_cache': json.dumps(pos_config._get_url_to_cache(request.session.debug)),
            'use_lna': use_lna,
        }
        response = request.render('point_of_sale.index', context)
        response.headers['Cache-Control'] = 'no-store'
        return response
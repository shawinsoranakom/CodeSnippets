def session_info(self):
        user = self.env.user
        session_uid = request.session.uid
        version_info = odoo.service.common.exp_version()

        if session_uid:
            user_context = dict(self.env['res.users'].context_get())
            if user_context != request.session.context:
                request.session.context = user_context
        else:
            user_context = {}

        IrConfigSudo = self.env['ir.config_parameter'].sudo()
        max_file_upload_size = int(IrConfigSudo.get_param(
            'web.max_file_upload_size',
            default=DEFAULT_MAX_CONTENT_LENGTH,
        ))
        is_internal_user = user._is_internal()
        session_info = {
            "uid": session_uid,
            "is_system": user._is_system() if session_uid else False,
            "is_admin": user._is_admin() if session_uid else False,
            "is_public": user._is_public(),
            "is_internal_user": is_internal_user,
            "user_context": user_context,
            "db": self.env.cr.dbname,
            "registry_hash": hmac(self.env(su=True), "webclient-cache", self.env.registry.registry_sequence),
            "user_settings": self.env['res.users.settings']._find_or_create_for_user(user)._res_users_settings_format(),
            "server_version": version_info.get('server_version'),
            "server_version_info": version_info.get('server_version_info'),
            "support_url": "https://www.odoo.com/buy",
            "name": user.name,
            "username": user.login,
            "quick_login": str2bool(IrConfigSudo.get_param('web.quick_login', default=True), True),
            "partner_write_date": fields.Datetime.to_string(user.partner_id.write_date),
            "partner_display_name": user.partner_id.display_name,
            "partner_id": user.partner_id.id if session_uid and user.partner_id else None,
            "web.base.url": IrConfigSudo.get_param('web.base.url', default=''),
            "active_ids_limit": int(IrConfigSudo.get_param('web.active_ids_limit', default='20000')),
            'profile_session': request.session.get('profile_session'),
            'profile_collectors': request.session.get('profile_collectors'),
            'profile_params': request.session.get('profile_params'),
            "max_file_upload_size": max_file_upload_size,
            "home_action_id": user.action_id.id,
            "currencies": self.env['res.currency'].get_all_currencies(),
            'bundle_params': {
                'lang': request.session.context['lang'],
            },
            'test_mode': config['test_enable'],
            'view_info': self.env['ir.ui.view'].get_view_info(),
            'groups': {
                'base.group_allow_export': user.has_group('base.group_allow_export') if session_uid else False,
            },
        }
        if request.session.debug:
            session_info['bundle_params']['debug'] = request.session.debug
        if is_internal_user:
            # We need sudo since a user may not have access to ancestor companies
            # We use `_get_company_ids` because it is cached and we sudo it because env.user return a sudo user.
            user_companies = self.env['res.company'].browse(user._get_company_ids()).sudo()
            disallowed_ancestor_companies_sudo = user_companies.parent_ids - user_companies
            all_companies_in_hierarchy_sudo = disallowed_ancestor_companies_sudo + user_companies
            session_info.update({
                # current_company should be default_company
                "user_companies": {
                    'current_company': user.company_id.id,
                    'allowed_companies': {
                        comp.id: {
                            'id': comp.id,
                            'name': comp.name,
                            'sequence': comp.sequence,
                            'child_ids': (comp.child_ids & all_companies_in_hierarchy_sudo).ids,
                            'parent_id': comp.parent_id.id,
                            'currency_id': comp.currency_id.id,
                        } for comp in user_companies
                    },
                    'disallowed_ancestor_companies': {
                        comp.id: {
                            'id': comp.id,
                            'name': comp.name,
                            'sequence': comp.sequence,
                            'child_ids': (comp.child_ids & all_companies_in_hierarchy_sudo).ids,
                            'parent_id': comp.parent_id.id,
                        } for comp in disallowed_ancestor_companies_sudo
                    },
                },
                "show_effect": True,
            })
        return session_info
def _verify_authorization(self, access_token, table_identifier, order):
        """
        Similar to _verify_pos_config but also looks for the restaurant.table of the given identifier.
        The restaurant.table record is also returned with reduced privileges.
        """
        pos_config = self._verify_pos_config(access_token)
        table_sudo = request.env["restaurant.table"].sudo().search([('identifier', '=', table_identifier)], limit=1)
        preset = request.env['pos.preset'].sudo().browse(order.get('preset_id'))
        is_takeaway = order and pos_config.use_presets and preset and preset.service_at != 'table'
        if not table_sudo and not pos_config.self_ordering_mode == 'kiosk' and pos_config.self_ordering_service_mode == 'table' and not is_takeaway:
            raise Unauthorized("Table not found")

        company = pos_config.company_id
        user = pos_config.self_ordering_default_user_id
        table = table_sudo.sudo(False).with_company(company).with_user(user).with_context(allowed_company_ids=company.ids)
        return pos_config, table
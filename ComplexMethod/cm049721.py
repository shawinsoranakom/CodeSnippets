def write(self, vals):
        res = super().write(vals)
        if (
            not self.env.context.get('disable_iap_update')
            and any(warning_attribute in vals for warning_attribute in ('warning_threshold', 'warning_user_ids'))
        ):
            route = '/iap/1/update-warning-email-alerts'
            endpoint = iap_tools.iap_get_endpoint(self.env)
            url = url_join(endpoint, route)
            for account in self:
                data = {
                    'account_token': account.sudo().account_token,
                    'warning_threshold': account.warning_threshold,
                    'warning_emails': [{
                        'email': user.email,
                        'lang_code': user.lang or get_lang(self.env).code,
                    } for user in account.warning_user_ids],
                }
                try:
                    iap_tools.iap_jsonrpc(url=url, params=data)
                except AccessError as e:
                    _logger.warning("Update of the warning email configuration has failed: %s", str(e))
        return res
def _get_account_information_from_iap(self):
        # During testing, we don't want to call the iap server
        if module.current_test:
            return
        route = '/iap/1/get-accounts-information'
        endpoint = iap_tools.iap_get_endpoint(self.env)
        url = url_join(endpoint, route)
        params = {
            'iap_accounts': [{
                'token': account.sudo().account_token,
                'service': account.service_id.technical_name,
            } for account in self if account.service_id],
            'dbuuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
        }
        try:
            accounts_information = iap_tools.iap_jsonrpc(url=url, params=params)
        except AccessError as e:
            _logger.warning("Fetch of the IAP accounts information has failed: %s", str(e))
            return

        for token, information in accounts_information.items():
            information.pop('link_to_service_page', None)
            accounts = self.filtered(lambda acc: secrets.compare_digest(acc.sudo().account_token, token))

            for account in accounts:
                # Default rounding of 4 decimal places to avoid large decimals
                balance_amount = round(information['balance'], None if account.service_id.integer_balance else 4)
                balance = f"{balance_amount} {account.service_id.unit_name or ''}"

                account_info = self._get_account_info(account, balance, information)
                account.with_context(disable_iap_update=True, tracking_disable=True).write(account_info)
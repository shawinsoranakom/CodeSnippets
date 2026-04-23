def _check_for_qr_code_errors(self, qr_method, amount, currency, debtor_partner, free_communication, structured_communication):
        if qr_method != 'emv_qr' or self.country_code != 'VN':
            return super()._check_for_qr_code_errors(qr_method, amount, currency, debtor_partner, free_communication, structured_communication)

        if not (self.partner_id.city or self.partner_id.state_id):
            return _("Missing Merchant City or State.")
        if not self.proxy_type:
            return _("Missing Proxy Type.")
        if self.proxy_type not in ['merchant_id', 'payment_service', 'atm_card', 'bank_acc']:
            return _("The proxy type %s is not supported for Vietnamese partners. It must be either Merchant ID, ATM Card Number or Bank Account", self.proxy_type)
        if not self.proxy_value:
            return _("Missing Proxy Value.")
        if not self._get_merchant_account_info():
            return _("Missing Merchant Account Information.")
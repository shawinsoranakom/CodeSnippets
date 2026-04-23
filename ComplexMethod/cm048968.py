def _check_kh_proxy(self):
        bakong_id_re = re.compile(r"^[a-zA-Z0-9_].*@[a-zA-Z0-9_].*$")
        for bank in self.filtered(lambda b: b.country_code == 'KH'):
            if bank.proxy_type not in ['bakong_id_solo', 'bakong_id_merchant', 'none', False]:
                raise ValidationError(_("The proxy type must be Bakong Account ID"))
            if bank.proxy_type in ['bakong_id_solo', 'bakong_id_merchant'] and (not bank.proxy_value or not bakong_id_re.match(bank.proxy_value) or len(bank.proxy_value) > 32):
                raise ValidationError(_("Please enter a valid Bakong Account ID."))
            if bank.proxy_type == 'bakong_id_merchant' and not bank.l10n_kh_merchant_id:
                raise ValidationError(_("Merchant ID is missing."))
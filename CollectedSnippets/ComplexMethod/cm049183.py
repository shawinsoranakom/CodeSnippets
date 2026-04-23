def _check_th_proxy(self):
        tax_id_re = re.compile(r'^[0-9]{13}$')
        mobile_re = re.compile(r'^[0-9]{10}$')
        for bank in self.filtered(lambda b: b.country_code == 'TH'):
            if bank.proxy_type not in ['ewallet_id', 'merchant_tax_id', 'mobile', 'none', False]:
                raise ValidationError(_("The QR Code Type must be either Ewallet ID, Merchant Tax ID or Mobile Number to generate a Thailand Bank QR code for account number %s.", bank.acc_number))
            if bank.proxy_type == 'merchant_tax_id' and (not bank.proxy_value or not tax_id_re.match(bank.proxy_value)):
                raise ValidationError(_("The Merchant Tax ID must be in the format 1234567890123 for account number %s.", bank.acc_number))
            if bank.proxy_type == 'mobile' and (not bank.proxy_value or not mobile_re.match(bank.proxy_value)):
                raise ValidationError(_("The Mobile Number must be in the format 0812345678 for account number %s.", bank.acc_number))
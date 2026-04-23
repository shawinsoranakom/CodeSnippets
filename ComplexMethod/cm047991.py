def _check_hk_proxy(self):
        auto_mobn_re = re.compile(r"^[+]\d{1,3}-\d{6,12}$")
        for bank in self.filtered(lambda b: b.country_code == 'HK'):
            if bank.proxy_type not in ['id', 'mobile', 'email', 'none', False]:
                raise ValidationError(_("The FPS Type must be either ID, Mobile or Email to generate a FPS QR code for account number %s.", bank.acc_number))
            if bank.proxy_type == 'id' and (not bank.proxy_value or len(bank.proxy_value) not in [7, 9]):
                raise ValidationError(_("Invalid FPS ID! Please enter a valid FPS ID with length 7 or 9 for account number %s.", bank.acc_number))
            if bank.proxy_type == 'mobile' and (not bank.proxy_value or not auto_mobn_re.match(bank.proxy_value)):
                raise ValidationError(_("Invalid Mobile! Please enter a valid mobile number with format +852-67891234 for account number %s.", bank.acc_number))
            if bank.proxy_type == 'email' and (not bank.proxy_value or not single_email_re.match(bank.proxy_value)):
                raise ValidationError(_("Invalid Email! Please enter a valid email address for account number %s.", bank.acc_number))
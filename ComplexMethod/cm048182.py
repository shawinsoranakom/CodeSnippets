def _check_br_proxy(self):
        for bank in self.filtered(lambda bank: bank.country_code == "BR" and bank.proxy_type != "none"):
            if bank.proxy_type not in ("email", "mobile", "br_cpf_cnpj", "br_random"):
                raise ValidationError(
                    _(
                        "The proxy type must be Email Address, Mobile Number, CPF/CNPJ (BR) or Random Key (BR) for Pix code generation."
                    )
                )

            value = bank.proxy_value
            if bank.proxy_type == "email" and not mail_validate(value):
                raise ValidationError(_("%s is not a valid email.", value))

            if bank.proxy_type == "br_cpf_cnpj" and (
                not self.partner_id.check_vat_br(value) or any(not char.isdecimal() for char in value)
            ):
                raise ValidationError(_("%s is not a valid CPF or CNPJ (don't include periods or dashes).", value))

            if bank.proxy_type == "mobile" and (not value or not value.startswith("+55") or len(value) != 14):
                raise ValidationError(
                    _(
                        "The mobile number %s is invalid. It must start with +55, contain a 2 digit territory or state code followed by a 9 digit number.",
                        value,
                    )
                )

            regex = r"%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}" % {"char": "[a-fA-F0-9]"}
            if bank.proxy_type == "br_random" and not re.fullmatch(regex, bank.proxy_value):
                raise ValidationError(
                    _(
                        "The random key %s is invalid, the format looks like this: 71d6c6e1-64ea-4a11-9560-a10870c40ca2",
                        value,
                    )
                )
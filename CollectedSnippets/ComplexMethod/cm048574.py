def _alias_prepare_alias_name(self, alias_name, name, code, jtype, company):
        """ Tool method generating standard journal alias, to ensure uniqueness
        and readability;  reset for other journals than purchase / sale """
        if jtype not in ('purchase', 'sale'):
            return False

        alias_name = next(
            (
                string for string in (alias_name, name, code, jtype)
                if (string and self.env['mail.alias']._is_encodable(string) and
                    self.env['mail.alias']._sanitize_alias_name(string))
            ), False
        )
        if company != self.env.ref('base.main_company'):
            company_identifier = self.env['mail.alias']._sanitize_alias_name(company.name) if self.env['mail.alias']._is_encodable(company.name) else company.id
            if f'-{company_identifier}' not in alias_name:
                alias_name = f"{alias_name}-{company_identifier}"
        return self.env['mail.alias']._sanitize_alias_name(alias_name)
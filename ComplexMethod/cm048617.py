def _validate_foreign_vat_country(self):
        for record in self:
            if record.foreign_vat:
                if not record.country_id:
                    raise ValidationError(_("The country of the foreign VAT number could not be detected. Please assign a country to the fiscal position."))
                if record.country_id == record.company_id.account_fiscal_country_id:
                    if not record.state_ids:
                        if record.company_id.account_fiscal_country_id.state_ids:
                            raise ValidationError(_("You cannot create a fiscal position with a foreign VAT within your fiscal country without assigning it a state."))
                if record.country_group_id and record.country_id:
                    if record.country_id not in record.country_group_id.country_ids:
                        raise ValidationError(_("You cannot create a fiscal position with a country outside of the selected country group."))

                similar_fpos_count = self.env['account.fiscal.position'].search_count([
                    *self.env['account.fiscal.position']._check_company_domain(record.company_id),
                    ('foreign_vat', 'not in', (False, record.foreign_vat)),
                    ('id', '!=', record.id),
                    ('country_id', '=', record.country_id.id),
                ])
                if similar_fpos_count:
                    raise ValidationError(_("A fiscal position with a foreign VAT already exists in this country."))
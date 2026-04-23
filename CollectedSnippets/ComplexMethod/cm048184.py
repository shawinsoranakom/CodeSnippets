def _enrich(self):
        """ This method calls the partner autocomplete service from IAP to enrich
        partner related fields of the company. """
        self.ensure_one()
        _logger.info("Starting enrich of company %s (%s)", self.name, self.id)

        company_domain = self._get_company_domain()
        if not company_domain:
            return False

        company_data = self.env['res.partner'].enrich_by_domain(company_domain, timeout=COMPANY_AC_TIMEOUT)
        if not company_data or company_data.get("error"):
            return False

        company_data = {field: value for field, value in company_data.items()
                        if field in self.partner_id._fields and value and (field == 'image_1920' or not self.partner_id[field])}

        # for company: from state_id / country_id display_name like to IDs
        company_data.update(self._enrich_extract_m2o_id(company_data, ['state_id', 'country_id']))

        self.partner_id.write(company_data)
        return True
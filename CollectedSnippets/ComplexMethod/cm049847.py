def create(self, vals_list):
        """ Create aliases using sudo if an alias is required, notably if its
        name is given. """
        # prefetch company information, used for alias domain
        company_fname = self._mail_get_company_field()
        if company_fname:
            company_id_default = self.default_get([company_fname]).get(company_fname) or self.env.company.id
            company_prefetch_ids = {vals[company_fname] for vals in vals_list if vals.get(company_fname)}
            company_prefetch_ids.add(company_id_default)
        else:
            company_id_default = self.env.company.id
            company_prefetch_ids = {company_id_default}

        # prepare all alias values
        alias_vals_list, record_vals_list = [], []
        for vals in vals_list:
            if vals.get('alias_name'):
                vals['alias_name'] = self.env['mail.alias']._sanitize_alias_name(vals['alias_name'])
            if self._require_new_alias(vals):
                company_id = vals.get(company_fname) or company_id_default
                company = self.env['res.company'].with_prefetch(company_prefetch_ids).browse(company_id)
                alias_vals, record_vals = self._alias_filter_fields(vals)
                # generate record-agnostic base alias values
                alias_vals.update(self.env[self._name].with_context(
                    default_alias_domain_id=alias_vals.get('alias_domain_id', company.alias_domain_id.id),
                )._alias_get_creation_values())
                alias_vals_list.append(alias_vals)
                record_vals_list.append(record_vals)

        # create all aliases
        alias_ids = []
        if alias_vals_list:
            alias_ids = iter(self.env['mail.alias'].sudo().create(alias_vals_list).ids)

        # update alias values in create vals directly
        valid_vals_list = []
        record_vals_iter = iter(record_vals_list)
        for vals in vals_list:
            if self._require_new_alias(vals):
                record_vals = next(record_vals_iter)
                record_vals['alias_id'] = next(alias_ids)
                valid_vals_list.append(record_vals)
            else:
                valid_vals_list.append(vals)

        records = super().create(valid_vals_list)

        # update alias values with values coming from record, post-create to have
        # access to all its values (notably its ID)
        records_walias = records.filtered('alias_id')
        for record in records_walias:
            alias_values = record._alias_get_creation_values()
            record.alias_id.sudo().write(alias_values)

        return records
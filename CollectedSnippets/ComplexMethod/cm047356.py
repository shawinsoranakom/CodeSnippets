def create(self, vals_list):
        if self.env.context.get('import_file'):
            self._check_import_consistency(vals_list)
        for vals in vals_list:
            if vals.get('website'):
                vals['website'] = self._clean_website(vals['website'])
            if vals.get('parent_id'):
                vals['company_name'] = False
        partners = super().create(vals_list)
        # due to ir.default, compute is not called as there is a default value
        # hence calling the compute manually
        for partner, values in zip(partners, vals_list):
            if 'lang' not in values and partner.parent_id:
                partner._compute_lang()

        if self.env.context.get('_partners_skip_fields_sync'):
            return partners

        for partner, vals in zip(partners, vals_list):
            vals = self.env['res.partner']._add_missing_default_values(vals)
            partner._fields_sync(vals)
        return partners
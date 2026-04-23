def create(self, vals_list):

        # create missing partners
        no_partner_vals_list = [
            vals
            for vals in vals_list
            if vals.get('name') and not vals.get('partner_id')
        ]
        if no_partner_vals_list:
            partners = self.env['res.partner'].with_context(default_parent_id=False).create([
                {
                    'name': vals['name'],
                    'is_company': True,
                    'image_1920': vals.get('logo'),
                    'email': vals.get('email'),
                    'phone': vals.get('phone'),
                    'website': vals.get('website'),
                    'vat': vals.get('vat'),
                    'country_id': vals.get('country_id'),
                }
                for vals in no_partner_vals_list
            ])
            # compute stored fields, for example address dependent fields
            partners.flush_model()
            for vals, partner in zip(no_partner_vals_list, partners):
                vals['partner_id'] = partner.id

        for vals in vals_list:
            # Copy delegated fields from root to branches
            if parent := self.browse(vals.get('parent_id')):
                for fname in self._get_company_root_delegated_field_names():
                    vals.setdefault(fname, self._fields[fname].convert_to_write(parent[fname], parent))

        self.env.registry.clear_cache()
        companies = super().create(vals_list)

        # The write is made on the user to set it automatically in the multi company group.
        if companies:
            (self.env.user | self.env['res.users'].browse(SUPERUSER_ID)).write({
                'company_ids': [Command.link(company.id) for company in companies],
            })

        # Make sure that the selected currencies are enabled
        companies.currency_id.sudo().filtered(lambda c: not c.active).active = True

        companies_needs_l10n = companies.filtered('country_id')
        if companies_needs_l10n:
            companies_needs_l10n.install_l10n_modules()

        return companies
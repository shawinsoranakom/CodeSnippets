def write(self, vals):
        if 'parent_id' in vals:
            raise UserError(self.env._("The company hierarchy cannot be changed."))

        if vals.get('currency_id'):
            currency = self.env['res.currency'].browse(vals['currency_id'])
            if not currency.active:
                currency.write({'active': True})

        res = super().write(vals)
        invalidation_fields = self.cache_invalidation_fields()
        asset_invalidation_fields = {'font', 'primary_color', 'secondary_color', 'external_report_layout_id'}

        companies_needs_l10n = (
            vals.get('country_id')
            and self.filtered(lambda company: not company.country_id)
        ) or self.browse()
        if not invalidation_fields.isdisjoint(vals):
            self.env.registry.clear_cache()

        if not asset_invalidation_fields.isdisjoint(vals):
            # this is used in the content of an asset (see asset_styles_company_report)
            # and thus needs to invalidate the assets cache when this is changed
            self.env.registry.clear_cache('assets')  # not 100% it is useful a test is missing if it is the case

        # Archiving a company should also archive all of its branches
        if vals.get('active') is False:
            self.child_ids.active = False

        for company in self:
            # Copy modified delegated fields from root to branches
            if (changed := set(vals) & set(self._get_company_root_delegated_field_names())) and not company.parent_id:
                branches = self.sudo().search([
                    ('id', 'child_of', company.id),
                    ('id', '!=', company.id),
                ])

                changed_vals = {
                    fname: self._fields[fname].convert_to_write(company[fname], branches)
                    for fname in sorted(changed)
                }
                branches.write(changed_vals)

        if companies_needs_l10n:
            companies_needs_l10n.install_l10n_modules()

        # invalidate company cache to recompute address based on updated partner
        company_address_fields = self._get_company_address_field_names()
        company_address_fields_upd = set(company_address_fields) & set(vals.keys())
        if company_address_fields_upd:
            self.invalidate_model(company_address_fields)
        return res
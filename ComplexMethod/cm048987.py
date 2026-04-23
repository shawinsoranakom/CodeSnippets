def _l10n_ec_setup_location_accounts(self, companies):
        loss_locs = dict(self.env['stock.location']._read_group(domain=[('usage', '=', 'inventory')], groupby=['company_id', 'id']))
        prod_locs = dict(self.env['stock.location']._read_group(domain=[('usage', '=', 'production')], groupby=['company_id', 'id']))
        for company in companies:
            # get template data
            Template = self.env['account.chart.template'].with_company(company)
            template_code = company.chart_template
            full_data = Template._get_chart_template_data(template_code)
            template_data = full_data.pop('template_data')

            ref = template_data.get('loss_stock_valuation_account')
            if (loss_loc := loss_locs.get(company)) and (loss_loc_account := ref and Template.ref(ref, raise_if_not_found=False)):
                loss_loc.write({
                    'valuation_account_id': loss_loc_account.id,
                })

            ref = template_data.get('production_stock_valuation_account')
            if (prod_loc := prod_locs.get(company)) and (prod_loc_account := ref and Template.ref(ref, raise_if_not_found=False)):
                prod_loc.write({
                    'valuation_account_id': prod_loc_account.id,
                })
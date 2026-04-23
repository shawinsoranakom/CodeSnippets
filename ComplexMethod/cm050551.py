def _get_profitability_values(self):
        if not self.env.user.has_group('project.group_project_manager'):
            return {}, False
        profitability_items = self._get_profitability_items(False)
        if profitability_items and 'revenues' in profitability_items and 'costs' in profitability_items:  # sort the data values
            profitability_items['revenues']['data'] = sorted(profitability_items['revenues']['data'], key=lambda k: k['sequence'])
            profitability_items['costs']['data'] = sorted(profitability_items['costs']['data'], key=lambda k: k['sequence'])
        costs = sum(profitability_items['costs']['total'].values())
        revenues = sum(profitability_items['revenues']['total'].values())
        margin = revenues + costs
        to_bill_to_invoice = profitability_items['costs']['total']['to_bill'] + profitability_items['revenues']['total']['to_invoice']
        billed_invoiced = profitability_items['costs']['total']['billed'] + profitability_items['revenues']['total']['invoiced']
        expected_percentage, to_bill_to_invoice_percentage, billed_invoiced_percentage = 0, 0, 0
        if revenues:
            expected_percentage = formatLang(self.env, (margin / revenues) * 100, digits=0)
        if profitability_items['revenues']['total']['to_invoice']:
            to_bill_to_invoice_percentage = formatLang(self.env, (to_bill_to_invoice / profitability_items['revenues']['total']['to_invoice']) * 100, digits=0)
        if profitability_items['revenues']['total']['invoiced']:
            billed_invoiced_percentage = formatLang(self.env, (billed_invoiced / profitability_items['revenues']['total']['invoiced']) * 100, digits=0)
        profitability_values_dict = {
            'account_id': self.account_id,
            'costs': profitability_items['costs'],
            'revenues': profitability_items['revenues'],
            'expected_percentage': expected_percentage,
            'to_bill_to_invoice_percentage': to_bill_to_invoice_percentage,
            'billed_invoiced_percentage': billed_invoiced_percentage,
            'total': {
                'costs': costs,
                'revenues': revenues,
                'margin': margin,
                'margin_percentage': formatLang(self.env,
                                                not float_utils.float_is_zero(costs, precision_digits=2) and (margin / -costs) * 100 or 0.0,
                                                digits=0),
            },
            'labels': self._get_profitability_labels(),
        }
        show_profitability = bool(profitability_values_dict.get('account_id')
            and (profitability_values_dict.get('costs') or profitability_values_dict.get('revenues'))
        )
        return profitability_values_dict, show_profitability
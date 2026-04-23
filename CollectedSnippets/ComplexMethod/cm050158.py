def _l10n_ar_get_amounts(self, base_lines=None):
        """ Method used to prepare data to present amounts and taxes related amounts when creating an
        electronic invoice for argentinean and the txt files for digital VAT books. Only take into account the argentinean taxes """
        self.ensure_one()
        base_lines = base_lines or []
        profits_tax_group = self.env['account.chart.template'].with_company(self.company_id).ref(
            'tax_group_percepcion_ganancias',
            raise_if_not_found=False,
        )
        if not profits_tax_group:
            raise RedirectWarning(
                message=_(
                    "A required tax group could not be found (XML ID: %s).\n"
                    "Please reload your chart template in order to reinstall the required tax group.\n\n"
                    "Note: You might have to relink your existing taxes to this new tax group.",
                    'tax_group_percepcion_ganancias',
                ),
                action=self.env.ref('account.action_account_config').id,
                button_text=_("Accounting Settings"),
            )

        def tax_grouping_by_have_vat_afip_code(_arg_base_line, arg_tax_data):
            arg_tax_data = arg_tax_data or {'tax': self.env['account.tax']}
            return {'have_vat_afip_code': bool(arg_tax_data['tax'].tax_group_id.l10n_ar_vat_afip_code)}

        def tax_grouping_by_have_vat_afip_not_012(_arg_base_line, arg_tax_data):
            arg_tax_data = arg_tax_data or {'tax': self.env['account.tax']}
            return {'have_vat_afip_not_012': arg_tax_data['tax'].tax_group_id.l10n_ar_vat_afip_code not in (False, '0', '1', '2')}

        def tax_grouping_by_vat_afip_code(_arg_base_line, arg_tax_data):
            arg_tax_data = arg_tax_data or {'tax': self.env['account.tax']}
            return {'vat_afip_code': arg_tax_data['tax'].tax_group_id.l10n_ar_vat_afip_code}

        def tax_grouping_by_tribute_afip_code(_arg_base_line, arg_tax_data):
            arg_tax_data = arg_tax_data or {'tax': self.env['account.tax']}
            return {'tribute_afip_code': arg_tax_data['tax'].tax_group_id.l10n_ar_tribute_afip_code}

        def tax_grouping_by_in_profits_group(_arg_base_line, arg_tax_data):
            arg_tax_data = arg_tax_data or {'tax': self.env['account.tax']}
            return {'in_profits_group': arg_tax_data['tax'].tax_group_id == profits_tax_group}

        def tax_grouping_by_tribute_09_non_profit(_arg_base_line, arg_tax_data):
            arg_tax_data = arg_tax_data or {'tax': self.env['account.tax']}
            return {'tribute_09_non_profit': arg_tax_data['tax'].tax_group_id.l10n_ar_tribute_afip_code == '09' and
                                             arg_tax_data['tax'].tax_group_id != profits_tax_group}

        have_vat_afip_code_base_lines_aggregated_values = self.env['account.tax']._aggregate_base_lines_tax_details(base_lines, tax_grouping_by_have_vat_afip_code)
        have_vat_afip_not_012_base_lines_aggregated_values = self.env['account.tax']._aggregate_base_lines_tax_details(base_lines, tax_grouping_by_have_vat_afip_not_012)
        vat_afip_code_base_lines_aggregated_values = self.env['account.tax']._aggregate_base_lines_tax_details(base_lines, tax_grouping_by_vat_afip_code)
        tribute_afip_code_base_lines_aggregated_values = self.env['account.tax']._aggregate_base_lines_tax_details(base_lines, tax_grouping_by_tribute_afip_code)
        in_profits_group_base_lines_aggregated_values = self.env['account.tax']._aggregate_base_lines_tax_details(base_lines, tax_grouping_by_in_profits_group)
        tribute_09_non_profit_base_lines_aggregated_values = self.env['account.tax']._aggregate_base_lines_tax_details(base_lines, tax_grouping_by_tribute_09_non_profit)

        have_vat_afip_code_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(have_vat_afip_code_base_lines_aggregated_values)
        have_vat_afip_not_012_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(have_vat_afip_not_012_base_lines_aggregated_values)
        vat_afip_code_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(vat_afip_code_base_lines_aggregated_values)
        tribute_afip_code_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(tribute_afip_code_base_lines_aggregated_values)
        in_profits_group_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(in_profits_group_base_lines_aggregated_values)
        tribute_09_non_profit_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(tribute_09_non_profit_base_lines_aggregated_values)

        res = {
            'vat_amount': 0,
            'vat_taxable_amount': 0,
            'vat_exempt_base_amount': 0,
            'vat_untaxed_base_amount': 0,
            'not_vat_taxes_amount': 0,
            'iibb_perc_amount': 0,
            'mun_perc_amount': 0,
            'intern_tax_amount': 0,
            'other_taxes_amount': 0,
            'profits_perc_amount': 0,
            'vat_perc_amount': 0,
            'other_perc_amount': 0,
        }

        for grouping_key, values in have_vat_afip_code_aggregated_tax_details.items():
            if grouping_key['have_vat_afip_code']:
                res['vat_amount'] = values['tax_amount_currency']
            else:
                res['not_vat_taxes_amount'] = values['tax_amount_currency']

        for grouping_key, values in have_vat_afip_not_012_aggregated_tax_details.items():
            if grouping_key['have_vat_afip_not_012']:
                res['vat_taxable_amount'] = values['base_amount_currency']

        for grouping_key, values in vat_afip_code_aggregated_tax_details.items():
            if grouping_key['vat_afip_code'] == '2':
                res['vat_exempt_base_amount'] = values['base_amount_currency']
            elif grouping_key['vat_afip_code'] == '1':
                res['vat_untaxed_base_amount'] = values['base_amount_currency']

        for grouping_key, values in tribute_afip_code_aggregated_tax_details.items():
            if grouping_key['tribute_afip_code'] == '07':
                res['iibb_perc_amount'] = values['tax_amount_currency']
            elif grouping_key['tribute_afip_code'] == '08':
                res['mun_perc_amount'] = values['tax_amount_currency']
            elif grouping_key['tribute_afip_code'] == '04':
                res['intern_tax_amount'] = values['tax_amount_currency']
            elif grouping_key['tribute_afip_code'] == '99':
                res['other_taxes_amount'] = values['tax_amount_currency']
            elif grouping_key['tribute_afip_code'] == '06':
                res['vat_perc_amount'] = values['tax_amount_currency']

        for grouping_key, values in in_profits_group_aggregated_tax_details.items():
            if grouping_key['in_profits_group']:
                res['profits_perc_amount'] = values['tax_amount_currency']

        for grouping_key, values in tribute_09_non_profit_aggregated_tax_details.items():
            if grouping_key['tribute_09_non_profit']:
                res['tribute_09_non_profit'] = values['tax_amount_currency']

        if self.l10n_latam_document_type_id.l10n_ar_letter == 'C':
            res['vat_taxable_amount'] = self.amount_untaxed

        if self.move_type in ('out_refund', 'in_refund') and self.l10n_latam_document_type_id.code in self._get_l10n_ar_codes_used_for_inv_and_ref():
            for amount_key, amount_value in res.items():
                res[amount_key] = amount_value * -1

        for amount_key, amount_value in res.items():
            res[amount_key] = float_round(amount_value, precision_digits=2)

        return res
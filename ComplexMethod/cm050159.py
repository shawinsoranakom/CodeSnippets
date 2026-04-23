def _get_vat(self, base_lines=None):
        """ Applies on wsfe web service and in the VAT digital books """
        # if we are on a document that works invoice and refund and it's a refund, we need to export it as negative

        def tax_grouping_by_vat_afip_code(_arg_base_line, arg_tax_data):
            arg_tax_data = arg_tax_data or {'tax': self.env['account.tax']}
            return {'vat_afip_code': arg_tax_data['tax'].tax_group_id.l10n_ar_vat_afip_code}

        res = []
        base_lines = base_lines or self._get_rounded_base_and_tax_lines()[0]
        vat_afip_code_base_lines_aggregated_values = self.env['account.tax']._aggregate_base_lines_tax_details(base_lines, tax_grouping_by_vat_afip_code)
        vat_afip_code_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(vat_afip_code_base_lines_aggregated_values)
        amount_sign = 1

        if self.move_type in ('out_refund', 'in_refund') and self.l10n_latam_document_type_id.code in self._get_l10n_ar_codes_used_for_inv_and_ref():
            amount_sign = -1

        for grouping_key, values in vat_afip_code_aggregated_tax_details.items():
            if grouping_key['vat_afip_code'] not in (False, '0', '1', '2') and (values['base_amount_currency'] or values['tax_amount_currency']):
                res.append({
                    'Id': grouping_key['vat_afip_code'],
                    'BaseImp': float_round(amount_sign * values['base_amount_currency'], precision_digits=2),
                    'Importe': float_round(amount_sign * values['tax_amount_currency'], precision_digits=2),
                })
                if grouping_key['vat_afip_code'] == '3':
                    res[-1]['Importe'] = 0.0

        return res
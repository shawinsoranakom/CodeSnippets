def _get_importe_desglose_foreign_partner(self, base_lines, is_refund):
        AccountTax = self.env['account.tax']

        def tax_details_info_grouping_function(base_line, tax_data):
            if not tax_data:
                return None
            tax = tax_data['tax']

            return {
                'applied_tax_amount': tax.amount,
                'l10n_es_type': tax.l10n_es_type,
                'l10n_es_exempt_reason': tax.l10n_es_exempt_reason if tax.l10n_es_type == 'exento' else False,
                'l10n_es_bien_inversion': tax.l10n_es_bien_inversion,
                'is_reverse_charge': tax_data['is_reverse_charge'],
                'tax_scope': tax.tax_scope,
                'is_refund': base_line['is_refund'],
            }

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, tax_details_info_grouping_function)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)

        invoice_info = {}
        for scope, target_key in (('service', 'PrestacionServicios'), ('consu', 'Entrega')):
            service_values_list = [
                values
                for values in values_per_grouping_key.values()
                if values['grouping_key'] and values['grouping_key']['tax_scope'] == scope
            ]
            if service_values_list:
                tax_details_info = self._build_tax_details_info(service_values_list)
                invoice_info.setdefault('DesgloseTipoOperacion', {})[target_key] = {
                    **tax_details_info['sujeta_no_sujeta'],
                    'S1': tax_details_info['sujeto'],
                    'S2': tax_details_info['sujeto_isp'],
                }

        total_amount = 0.0
        total_retention = 0.0
        for values in values_per_grouping_key.values():
            if values['grouping_key'] and values['grouping_key']['l10n_es_type'] == 'retencion':
                total_retention += values['tax_amount']
            else:
                total_amount += values['tax_amount']

        # Aggregate the base lines again (with no grouping) to add the base amount to the total.
        def totals_grouping_function(base_line, tax_data):
            return True if tax_data else None

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, totals_grouping_function)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)

        for values in values_per_grouping_key.values():
            total_amount += values['base_amount']

        if is_refund:
            total_amount = -total_amount
            total_retention = -total_retention

        return {
            'invoice_info': invoice_info,
            'total_amount': total_amount,
            'total_retention': total_retention,
        }
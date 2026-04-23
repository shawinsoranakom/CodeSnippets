def _l10n_it_edi_add_base_lines_xml_values(self, base_lines_aggregated_values, is_downpayment):
        self.ensure_one()
        quantita_pd = min(self.env['account.move.line']._fields['quantity'].get_digits(self.env)[1], 8)
        for index, (base_line, aggregated_values) in enumerate(base_lines_aggregated_values, start=1):
            line = base_line['record']
            tax_details = base_line['tax_details']
            discount = base_line['discount']
            quantity = base_line['quantity']
            price_subtotal = base_line['price_subtotal'] = tax_details['raw_total_excluded_currency']
            it_values = base_line['it_values'] = {}

            # Description.
            # Down payment lines:
            # If there was a down paid amount that has been deducted from this move,
            # we need to put a reference to the down payment invoice in the DatiFattureCollegate tag
            description = line.name
            if not is_downpayment and price_subtotal < 0:
                downpayment_moves = line._get_downpayment_lines().move_id
                if downpayment_moves:
                    downpayment_moves_description = ', '.join(downpayment_moves.mapped('name'))
                    sep = ', ' if description else ''
                    description = f"{description}{sep}{downpayment_moves_description}"
            # Workaround: remove line breaks due to Tax Agency portal bug.
            # This deviates from Odoo's standard behavior and must be reviewed if the issue gets fixed.
            description = description and description.replace('\n', ' ').strip() or "NO NAME"

            # Price unit.
            if quantity:
                it_values['prezzo_unitario'] = base_line['gross_price_subtotal'] / quantity
            else:
                it_values['prezzo_unitario'] = 0.0
            if base_line['currency_id'] != self.company_currency_id:
                it_values['prezzo_unitario'] = it_values['prezzo_unitario'] / base_line['rate']

            # Discount.
            it_values['sconto_maggiorazione_list'] = []
            if discount:
                it_values['sconto_maggiorazione_list'] = [{
                    'tipo': 'SC' if discount > 0 else 'MG',
                    'percentuale': abs(discount),
                    'importo': None,
                }]

            # Tax rates.
            rates = it_values['aliquota_iva_list'] = []
            for values in aggregated_values.values():
                grouping_key = values['grouping_key']
                if not grouping_key or grouping_key['skip']:
                    continue

                rates.append(grouping_key['tax_amount_field'] if grouping_key['tax_amount_type_field'] == 'percent' else 0.0)

            # Tax exempt reason.
            vat_tax = base_line['tax_ids'].flatten_taxes_hierarchy().filtered(lambda t: t._l10n_it_filter_kind('vat') and t.amount >= 0)[:1]
            it_values['natura'] = vat_tax.l10n_it_exempt_reason or None

            # Other data.
            other_data_list = it_values['altri_dati_gestionali_list'] = []
            if base_line['currency_id'] != self.company_currency_id:
                other_data_list.extend([
                    {
                        'tipo_dato': 'DIVISA',
                        'riferimento_testo': base_line['currency_id'].name,
                        'riferimento_numero': tax_details['raw_total_excluded_currency'],
                        'riferimento_data': None,
                    },
                    {
                        'tipo_dato': 'CAMBIO',
                        'riferimento_testo': None,
                        'riferimento_numero': base_line['rate'],
                        'riferimento_data': self.invoice_date,
                    },
                ])

            it_values.update({
                'numero_linea': index,
                'descrizione': description,
                'prezzo_totale': tax_details['raw_total_excluded'],
                'quantita': quantity,
                'quantita_pd': quantita_pd,
                'ritenuta': None,
            })
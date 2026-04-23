def _l10n_eg_eta_prepare_invoice_lines_data(self, invoice, base_lines_aggregated_values):
        lines = []
        totals = {
            'discount_total': 0.0,
            'total_price_subtotal_before_discount' : 0.0,
        }
        for base_line, aggregated_values in base_lines_aggregated_values:
            line = base_line['record']
            tax_details = base_line['tax_details']
            price_unit = self._l10n_eg_edi_round(abs((line.balance / line.quantity) / (1 - (line.discount / 100.0)))) if line.quantity and line.discount != 100.0 else line.price_unit
            price_subtotal_before_discount = self._l10n_eg_edi_round(abs(line.balance / (1 - (line.discount / 100)))) if line.discount != 100.0 else self._l10n_eg_edi_round(price_unit * line.quantity)
            discount_amount = self._l10n_eg_edi_round(price_subtotal_before_discount - abs(line.balance))
            item_code = line.product_id.l10n_eg_eta_code or line.product_id.barcode
            lines.append({
                'description': line.name,
                'itemType': item_code.startswith('EG') and 'EGS' or 'GS1',
                'itemCode': item_code,
                'unitType': line.product_uom_id.l10n_eg_unit_code_id.code,
                'quantity': line.quantity,
                'internalCode': line.product_id.default_code or '',
                'valueDifference': 0.0,
                'totalTaxableFees': 0.0,
                'itemsDiscount': 0.0,
                'unitValue': {
                    'currencySold': invoice.currency_id.name,
                    'amountEGP': price_unit,
                },
                'discount': {
                    'rate': line.discount,
                    'amount': discount_amount,
                },
                'taxableItems': [
                    {
                        'taxType': grouping_key['tax_type'],
                        'amount': self._l10n_eg_edi_round(abs(tax_values['tax_amount'])),
                        'subType': grouping_key['sub_type'],
                        'rate': grouping_key['rate'],
                    }
                    for grouping_key, tax_values in aggregated_values.items()
                    if grouping_key
                ],
                'salesTotal': price_subtotal_before_discount,
                'netTotal': self._l10n_eg_edi_round(tax_details['total_excluded'] + tax_details['delta_total_excluded']),
                'total': self._l10n_eg_edi_round(tax_details['total_included']),
            })
            totals['discount_total'] += discount_amount
            totals['total_price_subtotal_before_discount'] += price_subtotal_before_discount
            if invoice.currency_id != self.env.ref('base.EGP'):
                lines[-1]['unitValue']['currencyExchangeRate'] = self._l10n_eg_edi_round(invoice._l10n_eg_edi_exchange_currency_rate())
                lines[-1]['unitValue']['amountSold'] = line.price_unit
        return lines, totals
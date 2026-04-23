def _l10n_es_edi_facturae_prepare_inv_line(self, base_line, aggregated_values):
        """
        Convert the invoice lines to a list of items required for the Facturae xml generation

        :return: A tuple containing the Face items, the taxes and the invoice totals data.
        """
        self.ensure_one()
        invoice_ref = self.ref and self.ref[:20]
        line = base_line['record']
        tax_details = base_line['tax_details']

        receiver_transaction_reference = (
            line.sale_line_ids.order_id.client_order_ref[:20]
            if 'sale_line_ids' in line._fields and line.sale_line_ids.order_id.client_order_ref
            else invoice_ref
        )

        xml_values = {
            'ReceiverTransactionReference': receiver_transaction_reference,
            'FileReference': invoice_ref,
            'ReceiverContractReference': invoice_ref,
            'FileDate': fields.Date.context_today(self),
            'ItemDescription': line.name,
            'Quantity': line.quantity,
            'UnitOfMeasure': line.product_uom_id.l10n_es_edi_facturae_uom_code,
            'DiscountsAndRebates': [],
            'Charges': [],
            'GrossAmount': float_round(tax_details['raw_total_excluded_currency'], precision_digits=8),
        }

        if line.discount == 100.0:
            raw_total_cost = line.price_unit * line.quantity
        else:
            raw_total_cost = tax_details['raw_total_excluded_currency'] / (1 - (line.discount / 100.0))
        xml_values['TotalCost'] = float_round(raw_total_cost, precision_digits=8)

        if line.quantity:
            xml_values['UnitPriceWithoutTax'] = float_round(raw_total_cost / line.quantity, precision_digits=8)
        else:
            xml_values['UnitPriceWithoutTax'] = 0.0

        discount_amount = xml_values['TotalCost'] - xml_values['GrossAmount']
        if float_compare(discount_amount, 0.0, precision_digits=8) > 0:
            xml_values['DiscountsAndRebates'].append({
                'DiscountReason': '/',
                'DiscountRate': f'{line.discount:.2f}',
                'DiscountAmount': discount_amount,
            })

        if float_compare(discount_amount, 0.0, precision_digits=8) < 0:
            xml_values['Charges'].append({
                'ChargeReason': '/',
                'ChargeRate': f'{-line.discount:.2f}',
                'ChargeAmount': -discount_amount,
            })
        xml_values['TaxesOutputs'] = [
            self._l10n_es_edi_facturae_get_tax_node_from_tax_data(values)
            for values in aggregated_values.values()
            if values['grouping_key'] and values['grouping_key'].amount >= 0.0
        ]
        xml_values['TaxesWithheld'] = [
            self._l10n_es_edi_facturae_get_tax_node_from_tax_data(values)
            for values in aggregated_values.values()
            if values['grouping_key'] and values['grouping_key'].amount < 0.0
        ]

        return xml_values
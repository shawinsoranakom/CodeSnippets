def _add_base_lines_edi_ids(self, vals):
        vals['base_lines_edi_ids'] = {}
        invoice = vals['invoice']
        if invoice.reversed_entry_id:
            DecimalPrecision = self.env['decimal.precision']
            invoice_vals = {
                **vals,
                'invoice': invoice.reversed_entry_id,
            }
            self._add_invoice_base_lines_vals(invoice_vals)
            invoice_edi_id_x_base_line = dict(enumerate(invoice_vals['base_lines'], 1))
            overflow_edi_id = len(invoice_edi_id_x_base_line) + 1

            refund_base_lines = filter(lambda l: not self._is_document_allowance_charge(l), vals['base_lines'])
            for line_idx, refund_base_line in enumerate(refund_base_lines, 1):
                matching_edi_ids = [
                    line_id for line_id, base_line in invoice_edi_id_x_base_line.items()
                    if base_line['product_id'] == refund_base_line['product_id']
                    and float_compare(base_line['price_unit'], refund_base_line['price_unit'], precision_digits=DecimalPrecision.precision_get('Product Price')) == 0
                    and float_compare(base_line['discount'], refund_base_line['discount'], precision_digits=DecimalPrecision.precision_get('Discount')) == 0
                    and float_compare(base_line['quantity'], refund_base_line['quantity'], precision_digits=DecimalPrecision.precision_get('Product Unit')) >= 0
                ]

                if matching_edi_ids:
                    edi_id = min(matching_edi_ids, key=lambda line_id: invoice_edi_id_x_base_line[line_id]['quantity'])
                    vals['base_lines_edi_ids'][line_idx] = edi_id
                    invoice_edi_id_x_base_line.pop(edi_id)
                else:
                    vals['base_lines_edi_ids'][line_idx] = overflow_edi_id
                    overflow_edi_id += 1
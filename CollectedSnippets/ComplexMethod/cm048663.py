def onchange(self, values, field_names, fields_spec):
        # Since only one field can be changed at the same time (the record is
        # saved when changing tabs) we can avoid building the snapshots for the
        # other field
        if 'line_ids' in field_names:
            values = {key: val for key, val in values.items() if key != 'invoice_line_ids'}
            fields_spec = {key: val for key, val in fields_spec.items() if key != 'invoice_line_ids'}
        elif 'invoice_line_ids' in field_names:
            values = {key: val for key, val in values.items() if key != 'line_ids'}
            fields_spec = {key: val for key, val in fields_spec.items() if key != 'line_ids'}
            # When product_id and price_unit are in values, values is reordered to make sure
            # that product_id is before price_unit because product_id is triggering an onchange
            # of price_unit that could override the one defined here if the product_id is set
            # after price_unit
            invoice_line_ids = values.get('invoice_line_ids')
            for invoice_line_idx, invoice_line in enumerate(invoice_line_ids):
                if (len(invoice_line) == 3 and invoice_line[0] == 1 and isinstance(invoice_line[2], dict) and
                    'product_id' in invoice_line[2] and 'price_unit' in invoice_line[2]
                ):
                    if isinstance(invoice_line, tuple):
                        invoice_line_ids[invoice_line_idx] = invoice_line = list(invoice_line)
                    invoice_line[2] = dict(sorted(invoice_line[2].items(), key=lambda item: item[0] != 'product_id'))
        return super().onchange(values, field_names, fields_spec)
def _compute_is_refund(self):
        for line in self:
            is_refund = False
            if line.move_id.move_type in ('out_refund', 'in_refund'):
                is_refund = True
            elif line.move_id.move_type == 'entry':
                if line.tax_repartition_line_id:
                    is_refund = line.tax_repartition_line_id.document_type == 'refund'
                else:
                    # If we have both purchase and sale taxes on a line (which can happen in bank rec).
                    # We choose invoice by default
                    tax_type = line.tax_ids.mapped('type_tax_use')
                    if 'sale' in tax_type and 'purchase' in tax_type:
                        is_refund = line.credit == 0
                    else:
                        tax_type = line.tax_ids[:1].type_tax_use
                        if (tax_type == 'sale' and line.credit == 0) or (tax_type == 'purchase' and line.debit == 0):
                            is_refund = True

                    if line.tax_ids and line.move_id.reversed_entry_id:
                        is_refund = not is_refund
            line.is_refund = is_refund
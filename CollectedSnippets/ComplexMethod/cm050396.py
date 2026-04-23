def _stock_account_get_last_step_stock_moves(self):
        """ Overridden from stock_account.
        Returns the stock moves associated to this invoice."""
        rslt = super()._stock_account_get_last_step_stock_moves()
        for invoice in self:
            if invoice.move_type not in ['out_invoice', 'out_refund']:
                continue
            if (invoice.move_type == 'out_invoice' or (
                invoice.move_type == 'out_refund' and any(invoice.invoice_line_ids.sale_line_ids.mapped('is_downpayment')))
            ):
                rslt += invoice.mapped('invoice_line_ids.sale_line_ids.move_ids').filtered(lambda x: x.state == 'done' and x.location_dest_id.usage == 'customer')
            else:
                rslt += invoice.mapped('reversed_entry_id.invoice_line_ids.sale_line_ids.move_ids').filtered(lambda x: x.state == 'done' and x.location_id.usage == 'customer')
                # Add refunds generated from the SO
                rslt += invoice.mapped('invoice_line_ids.sale_line_ids.move_ids').filtered(lambda x: x.state == 'done' and x.location_id.usage == 'customer')
        return rslt
def _recompute_qty_to_invoice(self, start_date, end_date):
        """ Recompute the qty_to_invoice field for product containing timesheets

            Search the existed timesheets between the given period in parameter.
            Retrieve the unit_amount of this timesheet and then recompute
            the qty_to_invoice for each current product.

            :param start_date: the start date of the period
            :param end_date: the end date of the period
        """
        lines_by_timesheet = self.filtered(lambda sol: sol.product_id and sol.product_id._is_delivered_timesheet())
        domain = Domain(lines_by_timesheet._timesheet_compute_delivered_quantity_domain())
        refund_account_moves = self.order_id.invoice_ids.filtered(lambda am: am.state == 'posted' and am.move_type == 'out_refund').reversed_entry_id
        timesheet_domain = Domain('timesheet_invoice_id', '=', False) | Domain('timesheet_invoice_id.state', '=', 'cancel')
        if refund_account_moves:
            credited_timesheet_domain = Domain('timesheet_invoice_id.state', '=', 'posted') & Domain('timesheet_invoice_id', 'in', refund_account_moves.ids)
            timesheet_domain |= credited_timesheet_domain
        domain &= timesheet_domain
        if start_date:
            domain &= Domain('date', '>=', start_date)
        if end_date:
            domain &= Domain('date', '<=', end_date)
        mapping = lines_by_timesheet.sudo()._get_delivered_quantity_by_analytic(domain)
        timesheet_uom = self.order_id.timesheet_encode_uom_id

        for line in lines_by_timesheet:
            qty_to_invoice = mapping.get(line.id, 0.0)
            if qty_to_invoice:
                unit_amount = sum(line.timesheet_ids.filtered(lambda ts: start_date <= ts.date <= end_date and not ts.timesheet_invoice_id).mapped('unit_amount'))
                units_to_invoice = timesheet_uom._compute_quantity(unit_amount, line.product_uom_id, rounding_method='HALF-UP')
                line.qty_to_invoice = units_to_invoice
            else:
                prev_inv_status = line.invoice_status
                line.qty_to_invoice = qty_to_invoice
                line.invoice_status = prev_inv_status
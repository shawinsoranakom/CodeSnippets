def _link_timesheets_to_invoice(self, start_date=None, end_date=None):
        """ Search timesheets from given period and link this timesheets to the invoice

            When we create an invoice from a sale order, we need to
            link the timesheets in this sale order to the invoice.
            Then, we can know which timesheets are invoiced in the sale order.
            :param start_date: the start date of the period
            :param end_date: the end date of the period
        """
        for line in self.filtered(lambda i: i.move_type == 'out_invoice' and i.state == 'draft').invoice_line_ids:
            sale_line_delivery = line.sale_line_ids.filtered(lambda sol: sol.product_id.invoice_policy == 'delivery' and sol.product_id.service_type == 'timesheet')
            if not start_date and not end_date:
                start_date, end_date = self._get_range_dates(sale_line_delivery.order_id)
            if sale_line_delivery:
                domain = Domain(line._timesheet_domain_get_invoiced_lines(sale_line_delivery))
                if start_date:
                    domain &= Domain('date', '>=', start_date)
                if end_date:
                    domain &= Domain('date', '<=', end_date)
                timesheets = self.env['account.analytic.line'].sudo().search(domain)
                timesheets.write({'timesheet_invoice_id': line.move_id.id})
def _task_get_page_view_values(self, task, access_token, **kwargs):
        values = super()._task_get_page_view_values(task, access_token, **kwargs)
        values['so_accessible'] = False
        try:
            if task.sale_order_id and self._document_check_access('sale.order', task.sale_order_id.id):
                values['so_accessible'] = True
                title = _('Quotation') if task.sale_order_id.state in ['draft', 'sent'] else _('Sales Order')
                values['task_link_section'].append({
                    'access_url': task.sale_order_id.get_portal_url(),
                    'title': title,
                })
        except (AccessError, MissingError):
            pass

        moves = request.env['account.move']
        invoice_ids = task.sale_order_id.invoice_ids
        if invoice_ids and request.env['account.move'].has_access('read'):
            moves = request.env['account.move'].search([('id', 'in', invoice_ids.ids)])
            values['invoices_accessible'] = moves.ids
            if moves:
                if len(moves) == 1:
                    task_invoice_url = moves.get_portal_url()
                    title = _('Invoice')
                else:
                    task_invoice_url = f'/my/tasks/{task.id}/orders/invoices'
                    title = _('Invoices')
                values['task_link_section'].append({
                    'access_url': task_invoice_url,
                    'title': title,
                })
        return values
def _compute_sale_order_id(self):
        for task in self:
            if not (task.allow_billable and task.sale_line_id):
                task.sale_order_id = False
                continue
            sale_order = (
                task.sale_line_id.order_id
                or task.project_id.sale_order_id
                or task.project_id.reinvoiced_sale_order_id
                or task.sale_order_id
            )
            if sale_order and not task.partner_id:
                task.partner_id = sale_order.partner_id
            consistent_partners = (
                sale_order.partner_id
                | sale_order.partner_invoice_id
                | sale_order.partner_shipping_id
            ).commercial_partner_id
            if task.partner_id.commercial_partner_id in consistent_partners:
                task.sale_order_id = sale_order
            else:
                task.sale_order_id = False
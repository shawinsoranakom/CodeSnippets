def _action_cancel(self):
        documents = None
        for sale_order in self:
            if sale_order.state == 'sale' and sale_order.order_line:
                sale_order_lines_quantities = {order_line: (order_line.product_uom_qty, 0) for order_line in sale_order.order_line}
                documents = self.env['stock.picking'].with_context(include_draft_documents=True)._log_activity_get_documents(sale_order_lines_quantities, 'move_ids', 'UP')
        self.picking_ids.filtered(lambda p: p.state != 'done').with_context(skip_cancel_activity=True).action_cancel()
        if documents:
            filtered_documents = {}
            for (parent, responsible), rendering_context in documents.items():
                if parent._name == 'stock.picking':
                    if parent.state == 'cancel':
                        continue
                filtered_documents[(parent, responsible)] = rendering_context
            self._log_decrease_ordered_quantity(filtered_documents, cancel=True)
        return super()._action_cancel()
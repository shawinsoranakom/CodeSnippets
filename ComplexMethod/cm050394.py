def write(self, vals):
        values = vals
        if values.get('order_line') and self.state == 'sale':
            for order in self:
                pre_order_line_qty = {order_line: order_line.product_uom_qty for order_line in order.mapped('order_line') if not order_line.is_expense}

        if values.get('partner_shipping_id') and self.env.context.get('update_delivery_shipping_partner'):
            for order in self:
                order.picking_ids.partner_id = values.get('partner_shipping_id')
        elif values.get('partner_shipping_id'):
            new_partner = self.env['res.partner'].browse(values.get('partner_shipping_id'))
            for record in self:
                picking = record.mapped('picking_ids').filtered(lambda x: x.state not in ('done', 'cancel'))
                message = _("""The delivery address has been changed on the Sales Order<br/>
                        From <strong>"%(old_address)s"</strong> to <strong>"%(new_address)s"</strong>,
                        You should probably update the partner on this document.""",
                            old_address=record.partner_shipping_id.display_name, new_address=new_partner.display_name)
                picking.activity_schedule('mail.mail_activity_data_warning', note=message, user_id=self.env.user.id)

        if 'commitment_date' in values:
            # protagate commitment_date as the deadline of the related stock move.
            # TODO: Log a note on each down document
            deadline_datetime = values.get('commitment_date')
            for order in self:
                moves = order.order_line.move_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel') and m.location_dest_id.usage == 'customer'
                )
                moves.date_deadline = deadline_datetime or order.expected_date

        res = super().write(values)
        if values.get('order_line') and self.state == 'sale':
            for order in self:
                to_log = {}
                order.order_line.fetch(['product_uom_id', 'product_uom_qty', 'display_type', 'is_downpayment'])
                for order_line in order.order_line:
                    if order_line.display_type or order_line.is_downpayment:
                        continue
                    if float_compare(order_line.product_uom_qty, pre_order_line_qty.get(order_line, 0.0), precision_rounding=order_line.product_uom_id.rounding) < 0:
                        to_log[order_line] = (order_line.product_uom_qty, pre_order_line_qty.get(order_line, 0.0))
                if to_log:
                    documents = self.env['stock.picking'].sudo()._log_activity_get_documents(to_log, 'move_ids', 'UP')
                    documents = {k: v for k, v in documents.items() if k[0].state != 'cancel'}
                    order._log_decrease_ordered_quantity(documents)
        return res
def action_pos_order_cancel(self):
        draft_orders = self.filtered(lambda o: o.state == 'draft')
        if self.env.context.get('active_ids'):
            orders = self.browse(self.env.context.get('active_ids'))
            order_is_in_futur = any(order.preset_time and order.preset_time.date() > fields.Date.today() for order in orders)
            if order_is_in_futur:
                raise UserError(_('The order delivery / pickup date is in the future. You cannot cancel it.'))
            if not draft_orders:
                raise UserError(_('This order has already been paid. You cannot set it back to draft or edit it.'))

        if draft_orders:
            draft_orders.write({'state': 'cancel'})
            for config in draft_orders.mapped('config_id'):
                config.notify_synchronisation(config.current_session_id.id, self.env.context.get('device_identifier', 0))

        return {
            'pos.order': self._load_pos_data_read(draft_orders, self.config_id)
        }
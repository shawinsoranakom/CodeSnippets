def write(self, vals):
        values = vals
        if values.get('date_planned'):
            new_date = fields.Datetime.to_datetime(values['date_planned'])
            self.filtered(lambda l: not l.display_type)._update_move_date_deadline(new_date)
        lines = self.filtered(lambda l: l.order_id.state == 'purchase'
                                        and not l.display_type)

        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        previous_product_qty = {line.id: line.product_qty for line in lines}
        result = super().write(values)
        if 'price_unit' in values:
            for line in lines:
                # Avoid updating kit components' stock.move
                moves = line.move_ids.filtered(lambda s: s.state not in ('cancel', 'done') and s.product_id == line.product_id)
                moves.write({'price_unit': line._get_stock_move_price_unit()})
        if 'product_qty' in values:
            lines = lines.filtered(lambda l: l.product_uom_id.compare(previous_product_qty[l.id], l.product_qty) != 0)
            lines.with_context(previous_product_qty=previous_product_uom_qty)._create_or_update_picking()
        valuation_trigger = ['price_unit', 'product_qty', 'product_uom']
        if any(field in valuation_trigger for field in values):
            self.move_ids.filtered(lambda m: m.is_valued)._set_value()
        return result
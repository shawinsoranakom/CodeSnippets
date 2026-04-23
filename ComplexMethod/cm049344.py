def _cart_update_order_line(self, order_line, quantity, **kwargs):
        self.ensure_one()
        order_line.ensure_one()

        if quantity <= 0:
            # Remove zero or negative lines
            order_line.unlink()
            return self.env['sale.order.line']

        # Update existing line
        update_values = self._prepare_order_line_update_values(order_line, quantity, **kwargs)
        if update_values:
            combo_item_lines = order_line.linked_line_ids.filtered('combo_item_id')
            if (
                order_line.product_type == 'combo'
                and combo_item_lines
                and 'product_uom_qty' in update_values
            ):
                # A combo product and its items should have the same quantity (by design). If the
                # requested quantity isn't available for one or more combo items, we should lower
                # the quantity of the combo product and its items to the maximum available quantity
                # of the combo item with the least available quantity.
                combo_quantity = quantity
                for item_line in combo_item_lines:
                    if quantity != item_line.product_uom_qty:
                        combo_item_quantity, _warning = self._verify_updated_quantity(
                            item_line,
                            item_line.product_id.id,
                            quantity,
                            uom_id=item_line.product_uom_id.id,
                            **kwargs
                        )
                        combo_quantity = min(combo_quantity, combo_item_quantity)
                for item_line in combo_item_lines:
                    if combo_quantity != item_line.product_uom_qty:
                        self.with_context(skip_cart_verification=True)._cart_update_line_quantity(
                            line_id=item_line.id, quantity=combo_quantity
                        )
                update_values['product_uom_qty'] = combo_quantity

            order_line.write(update_values)

            order_line._check_validity()

        return order_line
def write(self, vals):
        values = vals
        change_topping = 'topping_ids_1' in values or 'topping_ids_2' in values or 'topping_ids_3' in values
        merge_needed = 'note' in values or change_topping or 'state' in values
        default_location_id = self.env.user.last_lunch_location_id and self.env.user.last_lunch_location_id.id or False

        if merge_needed:
            lines_to_deactivate = self.env['lunch.order']
            for line in self:
                # Only write on topping_ids_1 because they all share the same table
                # and we don't want to remove all the records
                # _extract_toppings will pop topping_ids_1, topping_ids_2 and topping_ids_3 from values
                # This also forces us to invalidate the cache for topping_ids_2 and topping_ids_3 that
                # could have changed through topping_ids_1 without the cache knowing about it
                toppings = self._extract_toppings(values)
                if change_topping:
                    self.invalidate_model(['topping_ids_2', 'topping_ids_3'])
                    values['topping_ids_1'] = [(6, 0, toppings)]
                matching_lines = self._find_matching_lines({
                    'user_id': values.get('user_id', line.user_id.id),
                    'product_id': values.get('product_id', line.product_id.id),
                    'note': values.get('note', line.note or False),
                    'toppings': toppings,
                    'lunch_location_id': values.get('lunch_location_id', default_location_id),
                    'state': values.get('state'),
                })
                if matching_lines:
                    lines_to_deactivate |= line
                    matching_lines.update_quantity(line.quantity)
            lines_to_deactivate.write({'active': False})
            return super(LunchOrder, self - lines_to_deactivate).write(values)
        return super().write(values)
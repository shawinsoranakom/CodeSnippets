def infos(self, user_id=None, context=None):
        if context:
            request.update_context(**context)
        self._check_user_impersonification(user_id)
        user = request.env['res.users'].browse(user_id) if user_id else request.env.user

        infos = self._make_infos(user, order=False)

        lines = self._get_current_lines(user)
        if lines:
            translated_states = dict(request.env['lunch.order']._fields['state']._description_selection(request.env))
            lines = [{
                'id': line.id,
                'product': (line.product_id.id, line.product_id.name, float_repr(
                    float_round(line.product_id.price, 2) * line.quantity, 2),
                float_round(line.product_id.price, 2)),
                'toppings': [(topping.name, float_repr(float_round(topping.price, 2) * line.quantity, 2),
                float_round(topping.price, 2))
                    for topping in line.topping_ids_1 | line.topping_ids_2 | line.topping_ids_3],
                'quantity': line.quantity,
                'price': line.price,
                'raw_state': line.state,
                'state': translated_states[line.state],
                'date': line.date,
                'location': line.lunch_location_id.name,
                'note': line.note
                } for line in lines.sorted('date')]
            total = float_round(sum(line['price'] for line in lines), 2)
            paid_subtotal = float_round(sum(line['price'] for line in lines if line['raw_state'] != 'new'), 2)
            unpaid_subtotal = total - paid_subtotal
            infos.update({
                'total': float_repr(total, 2),
                'paid_subtotal': float_repr(paid_subtotal, 2),
                'unpaid_subtotal': float_repr(unpaid_subtotal, 2),
                'raw_state': self._get_state(lines),
                'lines': lines,
            })
        return infos
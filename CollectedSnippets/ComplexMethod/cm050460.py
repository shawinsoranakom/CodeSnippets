def write(self, vals):
        for order in self:
            if vals.get('state') and vals['state'] == 'paid' and order.name == '/':
                session = self.env['pos.session'].browse(vals['session_id']) if not self.session_id and vals.get('session_id') else False
                vals['name'] = self._compute_order_name(session)
            if vals.get('mobile'):
                vals['mobile'] = order._phone_format(number=vals.get('mobile'),
                        country=order.partner_id.country_id or self.env.company.country_id)
            if vals.get('has_deleted_line') is not None and self.has_deleted_line:
                del vals['has_deleted_line']
            allowed_vals = ['paid', 'done', 'invoiced']
            if vals.get('state') and vals['state'] not in allowed_vals and order.state in allowed_vals:
                raise UserError(_('This order has already been paid. You cannot set it back to draft or edit it.'))

        list_line = self._create_pm_change_log(vals)
        res = super().write(vals)
        for order in self:
            if vals.get('payment_ids'):
                order._compute_prices()
                totally_paid_or_more = order.currency_id.compare_amounts(order.amount_paid, order.amount_total)
                if totally_paid_or_more < 0 and order.state in ['paid', 'done']:
                    raise UserError(_('The paid amount is different from the total amount of the order.'))
                elif totally_paid_or_more > 0 and order.state == 'paid':
                    list_line.append(_("Warning, the paid amount is higher than the total amount. (Difference: %s)", formatLang(self.env, order.amount_paid - order.amount_total, currency_obj=order.currency_id)))
                if order.nb_print > 0 and any(command[0] in [0, 1] and command[2].get('payment_status') and command[2]['payment_status'] != 'cancelled' for command in vals.get('payment_ids')):
                    raise UserError(_('You cannot change the payment of a printed order.'))

        if len(list_line) > 0:
            body = _("Payment changes:")
            body += self._markup_list_message(list_line)
            for order in self:
                if vals.get('payment_ids'):
                    order.message_post(body=body)

        return res
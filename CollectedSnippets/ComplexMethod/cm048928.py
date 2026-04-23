def _check_pos_hash_integrity(self):
        """Checks that all posted or invoiced pos orders have still the same data as when they were posted
        and raises an error with the result.
        """
        def build_order_info(order):
            entry_reference = _('(Receipt ref.: %s)')
            order_reference_string = order.pos_reference and entry_reference % order.pos_reference or ''
            return [ctx_tz(order, 'date_order'), order.l10n_fr_hash, order.name, order_reference_string, ctx_tz(order, 'write_date')]

        msg_alert = ''
        report_dict = {}
        if self._is_accounting_unalterable():
            orders = self.with_context(prefetch_fields=False).env['pos.order'].search([('state', 'in', ['paid', 'done']), ('company_id', '=', self.id),
                                    ('l10n_fr_secure_sequence_number', '!=', 0)], order="l10n_fr_secure_sequence_number ASC")

            if not orders:
                msg_alert = (_('There isn\'t any order flagged for data inalterability yet for the company %s. This mechanism only runs for point of sale orders generated after the installation of the module France - Certification CGI 286 I-3 bis. - POS', self.env.company.name))
                raise UserError(msg_alert)

            previous_hash = u''
            corrupted_orders = []
            for order in orders:
                if order.l10n_fr_hash != order._compute_hash(previous_hash=previous_hash):
                    corrupted_orders.append(order.name)
                    msg_alert = (_('Corrupted data on point of sale order with id %s.', order.id))
                previous_hash = order.l10n_fr_hash
            orders.invalidate_recordset()

            orders_sorted_date = orders.sorted(lambda o: o.date_order)
            start_order_info = build_order_info(orders_sorted_date[0])
            end_order_info = build_order_info(orders_sorted_date[-1])

            report_dict.update({
                'first_order_name': start_order_info[2],
                'first_order_hash': start_order_info[1],
                'first_order_date': start_order_info[0],
                'last_order_name': end_order_info[2],
                'last_order_hash': end_order_info[1],
                'last_order_date': end_order_info[0],
            })
            corrupted_orders = ', '.join([o for o in corrupted_orders])
            return {
                'result': report_dict or 'None',
                'msg_alert': msg_alert or 'None',
                'printing_date': format_date(self.env,  Date.to_string( Date.today())),
                'corrupted_orders': corrupted_orders or 'None'
            }
        else:
            raise UserError(_('Accounting is not unalterable for the company %s. This mechanism is designed for companies where accounting is unalterable.', self.env.company.name))
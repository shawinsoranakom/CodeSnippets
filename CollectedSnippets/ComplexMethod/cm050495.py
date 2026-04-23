def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        bank_payment_method_diffs = bank_payment_method_diffs or {}
        record = self.ensure_one()
        if self.env.user.has_group('point_of_sale.group_pos_user'):
            record = record.sudo()
        data = {}
        if record.get_session_orders().filtered(lambda o: o.state != 'cancel') or record.statement_line_ids:
            self.cash_real_transaction = sum(self.sudo().statement_line_ids.mapped('amount'))
            if self.state == 'closed':
                raise UserError(_('This session is already closed.'))
            self._check_if_no_draft_orders()
            self._check_invoices_are_posted()
            cash_difference_before_statements = self.cash_register_difference
            if self.update_stock_at_closing:
                self._create_picking_at_end_of_session()
                self._get_closed_orders().filtered(lambda o: not o.is_total_cost_computed)._compute_total_cost_at_session_closing(self.picking_ids.move_ids)
            # when the user is POS, update the record in sudo
            data = record.with_company(record.company_id).with_context(
                check_move_validity=False, skip_invoice_sync=True
            )._create_account_move(balancing_account, amount_to_balance, bank_payment_method_diffs)

            balance = sum(record.move_id.line_ids.mapped('balance'))
            try:
                with self.move_id._check_balanced({'records': self.move_id.sudo()}):
                    pass
            except UserError:
                # Creating the account move is just part of a big database transaction
                # when closing a session. There are other database changes that will happen
                # before attempting to create the account move, such as, creating the picking
                # records.
                # We don't, however, want them to be committed when the account move creation
                # failed; therefore, we need to roll back this transaction before showing the
                # close session wizard.
                self.env.cr.rollback()
                return self._close_session_action(balance)

            self.sudo()._post_statement_difference(cash_difference_before_statements)
            if record.move_id.line_ids:
                record.move_id.with_company(self.company_id)._post()
                # Set the uninvoiced orders' state to 'done'
                self.env['pos.order'].search([('session_id', '=', self.id), ('state', '=', 'paid')]).write({'state': 'done'})
            else:
                record.move_id.sudo().unlink()
            self.sudo().with_company(self.company_id)._reconcile_account_move_lines(data)
        else:
            self.sudo()._post_statement_difference(self.cash_register_difference)

        if self.config_id.order_edit_tracking:
            edited_orders = self.get_session_orders().filtered(lambda o: o.is_edited)
            if len(edited_orders) > 0:
                body = _("Edited order(s) during the session:%s",
                    Markup("<br/><ul>%s</ul>") % Markup().join(Markup("<li>%s</li>") % order._get_html_link() for order in edited_orders)
                )
                self.message_post(body=body)

        # Make sure to trigger reordering rules
        self.picking_ids.move_ids.sudo()._trigger_scheduler()

        self.write({'state': 'closed'})
        self.env.flush_all()  # ensure sale.report is up to date
        return True
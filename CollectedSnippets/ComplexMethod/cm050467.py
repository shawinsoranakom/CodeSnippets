def _create_misc_reversal_move(self, payment_moves):
        """ Create a misc move to reverse POS orders and "remove" it from the POS closing entry.
        This is done by taking data from the orders and using it to somewhat replicate the resulting entry in orders to
        reverse partially the movements done in the POS closing entry.
        """
        self.ensure_one()
        aml_values_list_per_nature = self._prepare_aml_values_list_per_nature()
        move_lines = []
        for aml_values_list in aml_values_list_per_nature.values():
            for aml_values in aml_values_list:
                aml_values['balance'] = -aml_values['balance']
                aml_values['amount_currency'] = -aml_values['amount_currency']
                move_lines.append(aml_values)

        # Make a move with all the lines.
        reversal_entry = self.env['account.move'].with_context(
            default_journal_id=self.config_id.journal_id.id,
            skip_invoice_sync=True,
            skip_invoice_line_sync=True,
        ).create({
            'journal_id': self.config_id.journal_id.id,
            'date': fields.Date.context_today(self),
            'ref': _('Reversal of POS closing entry %(entry)s for order %(order)s from session %(session)s', entry=self.session_move_id.name, order=self.name, session=self.session_id.name),
            'line_ids': [(0, 0, aml_value) for aml_value in move_lines],
            'reversed_pos_order_id': self.id
        })
        reversal_entry.action_post()

        partner = self.partner_id.commercial_partner_id
        accounts = (
            self.company_id.account_default_pos_receivable_account_id |
            self.payment_ids.mapped('payment_method_id.receivable_account_id') |
            partner.property_account_receivable_id
        )

        candidate_lines = reversal_entry.line_ids
        if payment_moves.line_ids:
            candidate_lines |= payment_moves.line_ids
        else:
            candidate_lines |= self.session_move_id.line_ids.filtered(
                lambda l: l.partner_id == partner and l.account_id == partner.property_account_receivable_id
            )

        lines_by_account = {}
        for line in candidate_lines:
            if line.account_id in accounts and not line.reconciled:
                lines_by_account.setdefault(line.account_id, self.env['account.move.line'])
                lines_by_account[line.account_id] |= line
        for lines in lines_by_account.values():
            lines.reconcile()
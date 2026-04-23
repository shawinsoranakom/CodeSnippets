def _validate_locks(self, values):
        """Check that the lock date changes are valid.
        * Check that we do not decrease or remove the hard lock dates.
        * Check there are no unreconciled bank statement lines in the period we want to lock.
        * Check there are no unhashed journal entires in the period we want to lock.
        :param vals: The values passed to the write method.
        """
        new_locks = {field: fields.Date.to_date(values[field])for field in LOCK_DATE_FIELDS if field in values}

        fiscalyear_lock_date = new_locks.get('fiscalyear_lock_date')
        hard_lock_date = new_locks.get('hard_lock_date')
        sale_lock_date = new_locks.get('sale_lock_date')
        purchase_lock_date = new_locks.get('purchase_lock_date')
        fiscal_lock_date = None
        if fiscalyear_lock_date or hard_lock_date:
            fiscal_lock_date = max(fiscalyear_lock_date or date.min, hard_lock_date or date.min)

        if 'hard_lock_date' in new_locks:
            for company in self:
                if not company.hard_lock_date:
                    continue
                if not hard_lock_date:
                    raise UserError(_("The Hard Lock Date cannot be removed."))
                if hard_lock_date < company.hard_lock_date:
                    raise UserError(_("A new Hard Lock Date must be posterior (or equal) to the previous one."))

        if hard_lock_date:
            draft_entries = self.env['account.move'].search([
                ('company_id', 'child_of', self.ids),
                ('state', '=', 'draft'),
                ('date', '<=', hard_lock_date)])
            if draft_entries:
                error_msg = _('There are still draft entries in the period you want to hard lock. You should either post or delete them.')
                action_error = {
                    'view_mode': 'list',
                    'name': _('Draft Entries'),
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', draft_entries.ids)],
                    'search_view_id': [self.env.ref('account.view_account_move_filter').id, 'search'],
                    'views': [[self.env.ref('account.view_move_tree_multi_edit').id, 'list'], [self.env.ref('account.view_move_form').id, 'form']],
                }
                raise RedirectWarning(error_msg, action_error, _('Show draft entries'))

        # Check for unreconciled bank statement lines
        if fiscal_lock_date:
            unreconciled_statement_lines = self.env['account.bank.statement.line'].search(
                self._get_unreconciled_statement_lines_domain(fiscal_lock_date)
            )
            if unreconciled_statement_lines:
                error_msg = _("There are still unreconciled bank statement lines in the period you want to lock."
                            "You should either reconcile or delete them.")
                action_error = self._get_unreconciled_statement_lines_redirect_action(unreconciled_statement_lines)
                raise RedirectWarning(error_msg, action_error, _('Show Unreconciled Bank Statement Line'))
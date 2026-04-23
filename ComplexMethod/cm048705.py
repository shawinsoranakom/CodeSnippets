def _compute_is_reconciled(self):
        """ Compute the field indicating if the statement lines are already reconciled with something.
        This field is used for display purpose (e.g. display the 'cancel' button on the statement lines).
        Also computes the residual amount of the statement line.
        """
        for st_line in self:
            _liquidity_lines, suspense_lines, _other_lines = st_line._seek_for_lines()

            # Compute residual amount
            if not st_line.checked:
                st_line.amount_residual = -st_line.amount_currency if st_line.foreign_currency_id else -st_line.amount
            elif suspense_lines.account_id.reconcile:
                st_line.amount_residual = sum(suspense_lines.mapped('amount_residual_currency'))
            else:
                st_line.amount_residual = sum(suspense_lines.mapped('amount_currency'))

            # Compute is_reconciled
            if not st_line.id:
                # New record: The journal items are not yet there.
                st_line.is_reconciled = False
            elif suspense_lines:
                # In case of the statement line comes from an older version, it could have a residual amount of zero.
                st_line.is_reconciled = suspense_lines.currency_id.is_zero(st_line.amount_residual)
            elif st_line.currency_id.is_zero(st_line.amount):
                st_line.is_reconciled = True
            else:
                # The journal entry seems reconciled.
                st_line.is_reconciled = True
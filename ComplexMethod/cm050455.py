def _assert_account_move(self, account_move, expected_account_move_vals):
        if expected_account_move_vals:
            # We allow partial checks of the lines of the account move if `line_ids_predicate` is specified.
            # This means that only those that satisfy the predicate are compared to the expected account move line_ids.
            line_ids_predicate = expected_account_move_vals.pop('line_ids_predicate', lambda _: True)
            line_ids = expected_account_move_vals.pop('line_ids')
            reconciliation_statuses = []
            for line in line_ids:
                partially_reconciled = line.pop('partially_reconciled', False)
                if partially_reconciled is True:
                    reconciliation_statuses.append('partially_reconciled')
                else:
                    reconciliation_statuses.append('fully_reconciled' if line.get('reconciled') else 'not_reconciled')
            account_move_line_ids = account_move.line_ids.filtered(line_ids_predicate)
            self.assertRecordValues(account_move_line_ids, line_ids)
            self.assertRecordValues(account_move, [expected_account_move_vals])

            # Check reconciliation status
            for line, reconciliation_status in zip(account_move_line_ids, reconciliation_statuses):
                # See 'account_move_line._compute_amount_residual'  for more explanation
                if reconciliation_status == 'fully_reconciled':
                    if line.matching_number:
                        self.assertTrue(line.full_reconcile_id)
                    self.assertAlmostEqual(line.amount_residual, 0)
                elif reconciliation_status == 'partially_reconciled':
                    self.assertFalse(line.full_reconcile_id)
                    if line.reconciled:
                        self.assertAlmostEqual(line.amount_residual, 0)
                    else:
                        self.assertGreater(abs(line.amount_residual), 0)
                elif reconciliation_status == 'not_reconciled':
                    self.assertFalse(line.full_reconcile_id)
                    self.assertFalse(line.reconciled)
        else:
            # if the expected_account_move_vals is falsy, the account_move should be falsy.
            self.assertFalse(account_move)
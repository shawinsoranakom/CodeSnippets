def _check_off_balance(self):
        for line in self.move_id.line_ids:
            if line.account_id.account_type == 'off_balance':
                if any(a.account_type != line.account_id.account_type for a in line.move_id.line_ids.account_id):
                    raise UserError(_('If you want to use "Off-Balance Sheet" accounts, all the accounts of the journal entry must be of this type'))
                if line.tax_ids or line.tax_line_id:
                    raise UserError(_('You cannot use taxes on lines with an Off-Balance account'))
                if line.reconciled:
                    raise UserError(_('Lines from "Off-Balance Sheet" accounts cannot be reconciled'))
def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' not in init_values:
            return super()._track_subtype(init_values)

        match self.state:
            case 'draft':
                return self.env.ref('hr_expense.mt_expense_reset')
            case 'cancel':
                return self.env.ref('hr_expense.mt_expense_refused')
            case 'paid':
                return self.env.ref('hr_expense.mt_expense_paid')
            case 'approved':
                if init_values['state'] in {'posted', 'in_payment', 'paid'}:  # Reverting state
                    subtype = 'hr_expense.mt_expense_entry_draft' if self.account_move_id else 'hr_expense.mt_expense_entry_delete'
                    return self.env.ref(subtype)
                return self.env.ref('hr_expense.mt_expense_approved')
            case _:
                return super()._track_subtype(init_values)
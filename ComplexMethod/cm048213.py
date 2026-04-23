def write(self, vals):
        if any(field in vals for field in {'is_editable', 'can_approve', 'can_refuse'}):
            raise UserError(_("You cannot edit the security fields of an expense manually"))

        if any(field in vals for field in {'tax_ids', 'analytic_distribution', 'account_id', 'manager_id'}):
            if any((not expense.is_editable and not self.env.su) for expense in self):
                raise UserError(_(
                    "Uh-oh! You can’t edit this expense.\n\n"
                    "Reach out to the administrators, flash your best smile, and see if they'll grant you the magical access you seek."
                ))

        res = super().write(vals)

        if vals.get('state') == 'approved' or vals.get('approval_state') == 'approved':
            self._check_can_approve()
        elif vals.get('state') == 'refused' or vals.get('approval_state') == 'refused':
            self._check_can_refuse()

        if 'currency_id' in vals:
            self._set_expense_currency_rate(date_today=fields.Date.context_today(self))
            for expense in self:
                expense.total_amount = expense.total_amount_currency * expense.currency_rate
        return res
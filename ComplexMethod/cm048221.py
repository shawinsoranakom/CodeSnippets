def _get_expense_account_destination(self):
        # account.move used to allow having several expenses with payment_mode = 'company_account'.
        # This method needs to support processing several expenses to allow reconciliation of old account.move.line
        ids = set()
        for expense in self:
            if expense.payment_mode == 'company_account':
                account_dest = expense.payment_method_line_id.payment_account_id or expense._get_outstanding_account_id()
            elif not expense.employee_id.sudo().work_contact_id:
                raise UserError(self.env._(
                    "No work contact found for the employee %(name)s, please configure one.",
                    name=expense.employee_id.name,
                ))
            else:
                partner = expense.employee_id.sudo().work_contact_id.with_company(expense.company_id)
                account_dest = partner.property_account_payable_id or partner.parent_id.property_account_payable_id
            ids.add(account_dest.id)

        # mimics <account.account>.id
        if not ids:
            return False
        if len(ids) > 1:
            raise UserError(self.env._(
                "The following expenses payment method leads to several accounts payable and this isn't supported:\n%(expenses)s",
                expenses=self.browse(ids),
            ))
        return ids.pop()
def action_split_expense(self):
        self.ensure_one()
        expense_split = self.expense_split_line_ids[0]
        copied_expenses = self.env["hr.expense"]
        if expense_split:
            self.expense_id.write(expense_split._get_values())

            self.expense_split_line_ids -= expense_split
            if self.expense_split_line_ids:
                for split in self.expense_split_line_ids:
                    copied_expenses |= self.expense_id.with_context({'from_split_wizard': True}).copy(split._get_values())

                attachment_ids = self.env['ir.attachment'].search([
                    ('res_model', '=', 'hr.expense'),
                    ('res_id', '=', self.expense_id.id)
                ])

                for copied_expense in copied_expenses:
                    for attachment in attachment_ids:
                        attachment.copy({'res_model': 'hr.expense', 'res_id': copied_expense.id})

        split_expense_ids = self.env['hr.expense']
        if self.expense_id.split_expense_origin_id:
            split_expense_ids = self.env['hr.expense'].search([('split_expense_origin_id', '=', self.expense_id.split_expense_origin_id.id)])
        (self.expense_id | copied_expenses).split_expense_origin_id = self.expense_id.split_expense_origin_id or self.expense_id
        all_related_expenses = copied_expenses | self.expense_id | split_expense_ids

        return all_related_expenses._get_records_action(name=_("Split Expenses"))
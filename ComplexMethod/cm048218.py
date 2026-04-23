def create_expense_from_attachments(self, attachment_ids=None, view_type='list'):
        """
            Create the expenses from files.

            :return: An action redirecting to hr.expense list view.
        """
        if not attachment_ids:
            raise UserError(_("No attachment was provided"))
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        expenses = self.env['hr.expense']

        if any(attachment.res_id or attachment.res_model != 'hr.expense' for attachment in attachments):
            raise UserError(_("Invalid attachments!"))

        product = self.env['product.product'].search([('can_be_expensed', '=', True)])
        if product:
            product = product.filtered(lambda p: p.default_code == "EXP_GEN")[:1] or product[0]
        else:
            raise UserError(_("You need to have at least one category that can be expensed in your database to proceed!"))

        for attachment in attachments:
            vals = {
                'name': self._get_untitled_expense_name(format_date(self.env, fields.Date.context_today(self))),
                'price_unit': 0,
                'product_id': product.id,
            }
            if product.property_account_expense_id:
                vals['account_id'] = product.property_account_expense_id.id
            expense = self.env['hr.expense'].create(vals)
            attachment.write({'res_model': 'hr.expense', 'res_id': expense.id})

            expense._message_set_main_attachment_id(attachment, force=True)
            expenses += expense
        return expenses.ids
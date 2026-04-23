def default_get(self, fields):
        # OVERRIDE
        res = super().default_get(fields)

        if 'line_ids' in fields and 'line_ids' not in res:

            # Retrieve moves to pay from the context.

            if self.env.context.get('active_model') == 'account.move':
                lines = self.env['account.move'].browse(self.env.context.get('active_ids', [])).line_ids
            elif self.env.context.get('active_model') == 'account.move.line':
                lines = self.env['account.move.line'].browse(self.env.context.get('active_ids', []))
            else:
                raise UserError(_(
                    "The register payment wizard should only be called on account.move or account.move.line records."
                ))

            if 'journal_id' in res and not self.env['account.journal'].browse(res['journal_id']).filtered_domain([
                *self.env['account.journal']._check_company_domain(lines.company_id),
                ('type', 'in', ('bank', 'cash', 'credit')),
            ]):
                # default can be inherited from the list view, should be computed instead
                del res['journal_id']

            # Keep lines having a residual amount to pay.
            available_lines = self.env['account.move.line']
            valid_account_types = self.env['account.payment']._get_valid_payment_account_types()
            for line in lines:

                if line.account_type not in valid_account_types:
                    continue
                if line.currency_id:
                    if line.currency_id.is_zero(line.amount_residual_currency):
                        continue
                else:
                    if line.company_currency_id.is_zero(line.amount_residual):
                        continue
                available_lines |= line

            # Check.
            if not available_lines:
                raise UserError(_("There's nothing left to pay for the selected journal items, so no payment registration is necessary. You've got your finances under control like a boss!"))
            if len(lines.company_id.root_id) > 1:
                raise UserError(_("You can't create payments for entries belonging to different companies."))
            if self._from_sibling_companies(lines) and lines.company_id.root_id not in self.env.user.company_ids:
                raise UserError(_("You can't create payments for entries belonging to different branches without access to parent company."))
            if len(set(available_lines.mapped('account_type'))) > 1:
                raise UserError(_("You can't register payments for both inbound and outbound moves at the same time."))

            res['line_ids'] = [(6, 0, available_lines.ids)]

        return res
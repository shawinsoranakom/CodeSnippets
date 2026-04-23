def _compute_l10n_it_payment_method(self):
        if self.env.company.account_fiscal_country_id.code != 'IT':
            return

        move_lines_per_matching_number = self.env['account.move.line'].search([
            ('matching_number', 'in', self.line_ids.filtered('matching_number').mapped('matching_number')),
            ('company_id', '=', self.env.company.id),
        ]).grouped('matching_number')

        for move in self:
            matching_numbers = move.line_ids.filtered('matching_number').mapped('matching_number')
            if matching_numbers:
                # We use matching_numbers[0] directly, assuming there's a valid key in the dictionary.
                matching_lines = move_lines_per_matching_number.get(matching_numbers[0])
                if matching_lines and matching_lines.payment_id:
                    payment_method_line = matching_lines.payment_id.payment_method_line_id[0]
                    if payment_method_line:
                        move.l10n_it_payment_method = payment_method_line.l10n_it_payment_method
                        continue  # Skip to the next move
            if linked_payment := move.matched_payment_ids.filtered(lambda p: p.state != 'draft')[:1]:
                move.l10n_it_payment_method = linked_payment.payment_method_line_id.l10n_it_payment_method
                continue

            # Default handling if no valid matching lines found or if conditions don't match
            move.l10n_it_payment_method = move.origin_payment_id.payment_method_line_id.l10n_it_payment_method or move.l10n_it_payment_method or 'MP05'
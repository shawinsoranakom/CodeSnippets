def _compute_payment_method_line_id(self):
        for wizard in self:
            if wizard.journal_id:
                available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)
            else:
                available_payment_method_lines = False

            if available_payment_method_lines and wizard.payment_method_line_id in available_payment_method_lines:
                continue

            # Select the first available one by default.
            if available_payment_method_lines:
                move_payment_method_lines = wizard.line_ids.move_id.preferred_payment_method_line_id
                if len(move_payment_method_lines) == 1 and move_payment_method_lines.id in available_payment_method_lines.ids:
                    wizard.payment_method_line_id = move_payment_method_lines
                else:
                    wizard.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                wizard.payment_method_line_id = False
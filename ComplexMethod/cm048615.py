def _synchronize_to_moves(self, changed_fields):
        '''
            Update the account.move regarding the modified account.payment.
            :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if not any(field_name in changed_fields for field_name in self._get_trigger_fields_to_synchronize()):
            return

        for pay in self:
            if pay.move_id.state == 'posted':
                continue
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            if 'amount' in changed_fields and len(liquidity_lines) > 1:
                raise UserError(_("You cannot change the amount of a payment with multiple liquidity lines."))

            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.
            write_off_line_vals = []
            if liquidity_lines and counterpart_lines and writeoff_lines:
                write_off_line_vals.append({
                    'name': writeoff_lines[0].name,
                    'account_id': writeoff_lines[0].account_id.id,
                    'partner_id': writeoff_lines[0].partner_id.id,
                    'currency_id': writeoff_lines[0].currency_id.id,
                    'amount_currency': sum(writeoff_lines.mapped('amount_currency')),
                    'balance': sum(writeoff_lines.mapped('balance')),
                })
            line_vals_per_type = pay._prepare_move_lines_per_type(write_off_line_vals=write_off_line_vals)
            line_ids_commands = []

            liquidity_lines_vals = line_vals_per_type.get('liquidity_lines', [])
            for liquidity_line, newline_val in zip_longest(liquidity_lines, liquidity_lines_vals):
                if liquidity_line and newline_val:
                    line_ids_commands.append(Command.update(liquidity_line.id, newline_val))
                elif not liquidity_line and newline_val:
                    line_ids_commands.append(Command.create(newline_val))
                elif liquidity_line and not newline_val:
                    line_ids_commands.append(Command.delete(liquidity_line.id))

            counterpart_lines_vals = line_vals_per_type.get('counterpart_lines', [])
            line_ids_commands.append(
                Command.update(counterpart_lines.id, counterpart_lines_vals[0])
                if counterpart_lines
                else Command.create(counterpart_lines_vals[0])
            )

            for line in writeoff_lines:
                line_ids_commands.append((2, line.id))
            for extra_line_vals in line_vals_per_type.get('write_off_lines', []) + line_vals_per_type.get('withholding_lines', []):
                line_ids_commands.append((0, 0, extra_line_vals))
            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.
            to_write = {
                'date': pay.date,
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands,
            }
            if 'journal_id' in changed_fields:
                to_write.update({
                    'name': '/',  # Set the name to '/' to allow it to be changed
                    'journal_id': pay.journal_id.id
                })
            pay.move_id.with_context(skip_invoice_sync=True).write(to_write)
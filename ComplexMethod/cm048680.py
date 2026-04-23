def action_switch_move_type(self):
        if any((move.posted_before and move.name) for move in self):
            raise ValidationError(_("You cannot switch the type of a document with an existing sequence number."))
        if any(move.move_type == "entry" for move in self):
            raise ValidationError(_("This action isn't available for this document."))

        for move in self:
            in_out, old_move_type = move.move_type.split('_')
            new_move_type = f"{in_out}_{'invoice' if old_move_type == 'refund' else 'refund'}"
            move.name = False
            move.write({
                'move_type': new_move_type,
                'currency_id': move.currency_id.id,
                'fiscal_position_id': move.fiscal_position_id.id,
            })
            if move.amount_total < 0:
                line_ids_commands = []
                for line in move.line_ids:
                    if line.display_type != 'product':
                        continue
                    line_ids_commands.append(Command.update(line.id, {
                        'quantity': -line.quantity,
                        'extra_tax_data': self.env['account.tax']._reverse_quantity_base_line_extra_tax_data(line.extra_tax_data),
                    }))
                move.write({'line_ids': line_ids_commands})
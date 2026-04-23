def _sanitize_vals(self, vals):
        if vals.get('invoice_line_ids') and vals.get('line_ids'):
            # values can sometimes be in only one of the two fields, sometimes in
            # both fields, sometimes one field can be explicitely empty while the other
            # one is not, sometimes not...
            update_vals = {
                line_id: line_vals[0]
                for command, line_id, *line_vals in vals['invoice_line_ids']
                if command == Command.UPDATE
            }
            for command, line_id, *line_vals in vals['line_ids']:
                if command == Command.UPDATE and line_id in update_vals:
                    line_vals[0].update(update_vals.pop(line_id))
            for line_id, line_vals in update_vals.items():
                vals['line_ids'] += [Command.update(line_id, line_vals)]
            for command, line_id, *line_vals in vals['invoice_line_ids']:
                assert command not in (Command.SET, Command.CLEAR)
                if [command, line_id, *line_vals] not in vals['line_ids']:
                    vals['line_ids'] += [(command, line_id, *line_vals)]
            del vals['invoice_line_ids']
        return vals
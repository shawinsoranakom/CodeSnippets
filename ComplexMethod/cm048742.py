def create(self, vals_list):
        moves = self.env['account.move'].browse({vals['move_id'] for vals in vals_list})
        container = {'records': self}
        move_container = {'records': moves}
        with moves._check_balanced(move_container),\
             ExitStack() as exit_stack,\
             self.env.protecting(self.env['account.move']._get_protected_vals({}, moves)), \
             moves._sync_dynamic_lines(move_container),\
             self._sync_invoice(container):
            lines = super().create([self._sanitize_vals(vals) for vals in vals_list])
            exit_stack.enter_context(self.env.protecting([protected for vals, line in zip(vals_list, lines) for protected in self.env['account.move']._get_protected_vals(vals, line)]))
            container['records'] = lines

        lines._check_tax_lock_date()

        if not self.env.context.get('tracking_disable'):
            # Log changes to move lines on each move
            tracked_fields = [fname for fname, f in self._fields.items() if hasattr(f, 'tracking') and f.tracking and not (hasattr(f, 'related') and f.related)]
            ref_fields = self.env['account.move.line'].fields_get(tracked_fields)
            empty_values = dict.fromkeys(tracked_fields)
            for move_id, modified_lines in lines.grouped('move_id').items():
                if not move_id.posted_before:
                    continue
                for line in modified_lines:
                    if tracking_value_ids := line._mail_track(ref_fields, empty_values)[1]:
                        line.move_id._message_log(
                            body=_("Journal Item %s created", line._get_html_link(title=f"#{line.id}")),
                            tracking_value_ids=tracking_value_ids
                        )

        lines.move_id._synchronize_business_models(['line_ids'])
        # Remove analytic lines created for draft AMLs, after analytic_distribution has been updated
        lines.filtered(lambda l: l.parent_state == 'draft').analytic_line_ids.with_context(skip_analytic_sync=True).unlink()
        return lines
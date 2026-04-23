def unlink(self):
        if not self:
            return True

        self.remove_move_reconcile()

        # Check the lock date. (Only relevant if the move is posted and non zero lines)
        non_zero_lines = self.filtered(lambda l: l.balance or l.amount_currency)
        moves_to_check = non_zero_lines.move_id.filtered(lambda m: m.state == 'posted')
        moves_to_check._check_fiscal_lock_dates()

        # Check the tax lock date.
        self._check_tax_lock_date()

        if not self.env.context.get('tracking_disable'):
            # Log changes to move lines on each move
            tracked_fields = [fname for fname, f in self._fields.items() if hasattr(f, 'tracking') and f.tracking and not (hasattr(f, 'related') and f.related)]
            ref_fields = self.env['account.move.line'].fields_get(tracked_fields)
            empty_line = self.browse([False])  # all falsy fields but not failing `ensure_one` checks
            for move_id, modified_lines in self.grouped('move_id').items():
                if not move_id.posted_before:
                    continue
                for line in modified_lines:
                    if tracking_value_ids := empty_line._mail_track(ref_fields, line)[1]:
                        line.move_id._message_log(
                            body=_("Journal Item %s deleted", line._get_html_link(title=f"#{line.id}")),
                            tracking_value_ids=tracking_value_ids
                        )

        move_container = {'records': self.move_id}
        with self.move_id._check_balanced(move_container),\
             self.move_id._sync_dynamic_lines(move_container):
            res = super().unlink()

        return res
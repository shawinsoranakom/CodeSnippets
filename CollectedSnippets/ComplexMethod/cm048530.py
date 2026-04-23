def _get_move_dict_vals_change_period(self):

        def get_lock_safe_date(aml):
            return self._get_lock_safe_date(aml.date)

        # set the change_period account on the selected journal items

        ref_format = self._get_cut_off_label_format()
        move_data = {'new_date': {
            'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
            'move_type': 'entry',
            'line_ids': [],
            'ref': self._format_strings(ref_format, self.move_line_ids[0].move_id),
            'date': fields.Date.to_string(self.date),
            'journal_id': self.journal_id.id,
            'adjusting_entry_origin_move_ids': self.move_line_ids.move_id.ids,
        }}
        # complete the account.move data
        for date, grouped_lines in groupby(self.move_line_ids, get_lock_safe_date):
            grouped_lines = list(grouped_lines)
            amount = sum(l.balance for l in grouped_lines)
            move_data[date] = {
                'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
                'move_type': 'entry',
                'line_ids': [],
                'ref': self._format_strings(ref_format, grouped_lines[0].move_id, amount),
                'date': fields.Date.to_string(date),
                'journal_id': self.journal_id.id,
                'adjusting_entry_origin_move_ids': self.move_line_ids.move_id.ids,
            }

        # compute the account.move.lines and the total amount per move
        for aml in self.move_line_ids:
            for date in ('new_date', get_lock_safe_date(aml)):
                move_data[date]['line_ids'] += self._get_move_line_dict_vals_change_period(aml, date)

        move_vals = [m for m in move_data.values()]
        return move_vals
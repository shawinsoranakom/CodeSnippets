def _format_strings(self, string, move, amount=None, account_source_name=''):
        return string.format(
            label=move.name or _('Adjusting Entry'),
            percent=float_repr(self.percentage, 2),
            name=move.name,
            id=move.id,
            amount=formatLang(self.env, abs(amount), currency_obj=self.company_id.currency_id) if amount else '',
            debit_credit=amount < 0 and _('C') or _('D') if amount else None,
            link=self._format_move_link(move),
            date=format_date(self.env, move.date),
            new_date=self.date and format_date(self.env, self.date) or _('[Not set]'),
            account_source_name=account_source_name,
            account_target_name=self.destination_account_id.display_name,
        )
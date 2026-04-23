def _compute_display_name(self):
        formatted_display_name = self.env.context.get('formatted_display_name')
        new_line = '\n'
        preferred_account_ids = self.env.context.get('preferred_account_ids', [])
        if (
            (move_type := self.env.context.get('move_type'))
            and (partner := self.env.context.get('partner_id'))
            and not preferred_account_ids
        ):
            preferred_account_ids = self._order_accounts_by_frequency_for_partner(self.env.company.id, partner, move_type)
        for account in self:
            if formatted_display_name and account.code:
                account.display_name = (
                    f"""{account.code if self.env.user.has_group('account.group_account_readonly') else ''} {account.name}"""
                    f"""{f' `{_("Suggested")}`' if account.id in preferred_account_ids else ''}"""
                    f"""{f'{new_line}--{account.description}--' if account.description else ''}"""
                )
            else:
                account.display_name = f"{account.code} {account.name}" if account.code and self.env.user.has_group('account.group_account_readonly') else account.name
def _check_constrains_account_id_journal_id(self):
        # Avoid using api.constrains for fields journal_id and account_id as in case of a write on
        # account move and account move line in the same operation, the check would be done
        # before all write are complete, causing a false positive
        for line in self.filtered(lambda x: x.display_type not in ('line_section', 'line_subsection', 'line_note')):
            account = line.account_id
            journal = line.move_id.journal_id

            if not (account.active or line.is_imported or self.env.context.get('skip_account_deprecation_check')):
                raise UserError(_('The account %(name)s (%(code)s) is archived.', name=account.name, code=account.code))

            account_currency = account.currency_id
            if account_currency and account_currency != line.company_currency_id and account_currency != line.currency_id:
                raise UserError(_('The account selected on your journal entry forces to provide a secondary currency. You should remove the secondary currency on the account.'))

            if account in (journal.default_account_id, journal.suspense_account_id):
                continue
def _ensure_code_is_unique(self):
        """ Check account codes per companies. These are the checks:

            1. Check that the code is set for each of the account's companies.

            2. Check that no child or parent companies have another account with the same code
               as the account.

               The definition of availability is the same as the one used by _search_new_account_code
               and both methods need to be kept in sync.
        """
        # Check 1: Check that the code is set.
        for account in self.sudo():
            for company in account.company_ids.root_id:
                if not account.with_company(company).code:
                    raise ValidationError(_("The code must be set for every company to which this account belongs."))

        # Check 2: Check that no child or parent companies have an account with the same code.

        # Do a grouping by companies in `company_ids`.
        account_ids_to_check_by_company = defaultdict(list)
        for account in self.sudo():
            companies_to_check = account.company_ids
            for company in companies_to_check:
                account_ids_to_check_by_company[company].append(account.id)

        for company, account_ids in account_ids_to_check_by_company.items():
            accounts = self.browse(account_ids).with_prefetch(self.ids).sudo()

            # Check 2.1: Check that there are no duplicates in the given recordset.
            accounts_by_code = accounts.with_company(company).grouped('code')
            duplicate_codes = None
            if len(accounts_by_code) < len(accounts):
                duplicate_codes = [code for code, accounts in accounts_by_code.items() if len(accounts) > 1]

            # Check 2.2: Check that there are no duplicates in database
            elif duplicates := self.with_company(company).sudo().with_context(active_test=False).search_fetch(
                [
                    ('code', 'in', list(accounts_by_code)),
                    ('id', 'not in', self.ids),
                    '|',
                    ('company_ids', 'parent_of', company.ids),
                    ('company_ids', 'child_of', company.ids),
                ],
                ['code_store'],
            ):
                duplicate_codes = duplicates.mapped('code')
            if duplicate_codes:
                raise ValidationError(
                    _("Account codes must be unique. You can't create accounts with these duplicate codes: %s", ", ".join(duplicate_codes))
                )
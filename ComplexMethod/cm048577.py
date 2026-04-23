def create(self, vals_list):
        for vals in vals_list:
            # have to keep track of new journal codes when importing
            codes = [vals['code'] for vals in vals_list if 'code' in vals] if 'import_file' in self.env.context else False
            self._fill_missing_values(vals, protected_codes=codes)

        journals = super(AccountJournal, self.with_context(mail_create_nolog=True)).create(vals_list)

        for journal, vals in zip(journals, vals_list):
            # Create the bank_account_id if necessary
            if journal.type == 'bank':
                if not journal.bank_account_id and vals.get('bank_acc_number'):
                    journal.set_bank_account(vals.get('bank_acc_number'), vals.get('bank_id'))
                if journal.bank_account_id and journal.bank_account_id._user_can_trust():
                    journal.bank_account_id.allow_out_payment = True

        return journals
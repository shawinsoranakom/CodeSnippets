def test_unmerge(self):
        company_1 = self.company_data['company']
        company_2 = self.company_data_2['company']

        # 1. Create a merged account.
        # First, set-up various fields pointing to the accounts before merging
        accounts = self.env['account.account']._load_records([
            {
                'xml_id': f'account.{company_1.id}_test_account_1',
                'values': {
                    'name': 'My First Account',
                    'code': '100234',
                    'account_type': 'asset_receivable',
                    'company_ids': [Command.link(company_1.id)],
                    'tax_ids': [Command.link(self.company_data['default_tax_sale'].id)],
                    'tag_ids': [Command.link(self.env.ref('account.account_tag_operating').id)],
                },
            },
            {
                'xml_id': f'account.{company_2.id}_test_account_2',
                'values': {
                    'name': 'My Second Account',
                    'code': '100235',
                    'account_type': 'asset_receivable',
                    'company_ids': [Command.link(company_2.id)],
                    'tax_ids': [Command.link(self.company_data_2['default_tax_sale'].id)],
                    'tag_ids': [Command.link(self.env.ref('account.account_tag_investing').id)],
                },
            },
        ])
        referencing_records = {
            account: self._create_references_to_account(account)
            for account in accounts
        }

        # Create the merged account by merging `accounts`
        wizard = self._create_account_merge_wizard(accounts)
        wizard.action_merge()
        self.assertFalse(accounts[1].exists())

        # Check that the merged account has correct values
        account_to_unmerge = accounts[0]
        self.assertRecordValues(account_to_unmerge, [{
            'company_ids': [company_1.id, company_2.id],
            'name': 'My First Account',
            'code': '100234',
            'tax_ids': [self.company_data['default_tax_sale'].id, self.company_data_2['default_tax_sale'].id],
            'tag_ids': [self.env.ref('account.account_tag_operating').id, self.env.ref('account.account_tag_investing').id],
        }])
        self.assertRecordValues(account_to_unmerge.with_company(company_2), [{'code': '100235'}])
        self.assertEqual(self.env['account.chart.template'].ref('test_account_1'), account_to_unmerge)
        self.assertEqual(self.env['account.chart.template'].with_company(company_2).ref('test_account_2'), account_to_unmerge)

        for referencing_records_for_account in referencing_records.values():
            for referencing_record, fname in referencing_records_for_account.items():
                expected_field_value = account_to_unmerge.ids if referencing_record._fields[fname].type == 'many2many' else account_to_unmerge.id
                self.assertRecordValues(referencing_record, [{fname: expected_field_value}])

        # Step 2: Unmerge the account
        new_account = account_to_unmerge.with_context({
            'account_unmerge_confirm': True,
            'allowed_company_ids': [company_1.id, company_2.id],
        })._action_unmerge()

        # Check that the account fields are correct
        self.assertRecordValues(account_to_unmerge, [{
            'company_ids': [company_1.id],
            'name': 'My First Account',
            'code': '100234',
            'tax_ids': self.company_data['default_tax_sale'].ids,
            'tag_ids': [self.env.ref('account.account_tag_operating').id, self.env.ref('account.account_tag_investing').id],
        }])
        self.assertRecordValues(account_to_unmerge.with_company(company_2), [{'code': False}])
        self.assertRecordValues(new_account.with_company(company_2), [{
            'company_ids': [company_2.id],
            'name': 'My First Account',
            'code': '100235',
            'tax_ids': self.company_data_2['default_tax_sale'].ids,
            'tag_ids': [self.env.ref('account.account_tag_operating').id, self.env.ref('account.account_tag_investing').id],
        }])
        self.assertRecordValues(new_account, [{'code': False}])

        # Check that the referencing records were correctly unmerged
        new_account_by_old_account = {
            account_to_unmerge: account_to_unmerge,
            accounts[1]: new_account,
        }
        for account, referencing_records_for_account in referencing_records.items():
            for referencing_record, fname in referencing_records_for_account.items():
                expected_account = new_account_by_old_account[account]
                expected_field_value = expected_account.ids if referencing_record._fields[fname].type == 'many2many' else expected_account.id
                self.assertRecordValues(referencing_record, [{fname: expected_field_value}])

        # Check that the XMLids were correctly unmerged
        self.assertEqual(self.env['account.chart.template'].ref('test_account_1'), account_to_unmerge)
        self.assertEqual(self.env['account.chart.template'].with_company(company_2).ref('test_account_2'), new_account)
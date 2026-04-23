def test_update_move_type_entry(self):
        """ Test that move of type 'entry' are correctly updated.
        If a line has a negative balance and use a sale tax, it should act as an invoice.
        If a line has a positive balance and use a sale tax, it should act as a refund.
        If a line has a negative balance and use a purchase tax, it should act as a refund.
        If a line has a positive balance and use a purchase tax, it should be treated as an invoice.
        """
        account = self.company_data['default_account_assets']  # Account is not relevant for the test but must be set.
        for tax_type in ['sale', 'purchase']:
            tax = self._create_tax(f'test_{tax_type}_tax', 10, type_tax_use=tax_type, tag_names=self.tag_names)
            for balance in [-1000, 1000]:
                with self.subTest(f'Testing move type entry {tax_type}: {balance}'):
                    move = self.env['account.move'].create({
                        'move_type': 'entry',
                        'line_ids': [
                            Command.create({
                                "name": "line name",
                                "account_id": account.id,
                                'tax_ids': [Command.set(tax.ids)],
                                "balance": balance,
                            }),
                        ]
                    })

                    self._change_tax_tag(tax, 'invoice_base_tag_changed', invoice=True, base=True)
                    self._change_tax_tag(tax, 'refund_base_tag_changed', invoice=False, base=True)

                    self.wizard.update_amls_tax_tags()
                    invoice_line, tax_line, _ = self._get_amls_by_type(move)
                    if (balance < 0 and tax_type == 'sale') or (balance > 0 and tax_type == 'purchase'):
                        self.assertEqual(invoice_line.tax_tag_ids.name, 'invoice_base_tag_changed')
                        self.assertEqual(tax_line.tax_tag_ids.name, 'invoice_tax_tag')
                    elif (balance < 0 and tax_type == 'purchase') or (balance > 0 and tax_type == 'sale'):
                        self.assertEqual(invoice_line.tax_tag_ids.name, 'refund_base_tag_changed')
                        self.assertEqual(tax_line.tax_tag_ids.name, 'refund_tax_tag')
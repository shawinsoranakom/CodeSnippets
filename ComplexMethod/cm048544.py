def create_line_for_reconciliation(self, balance, amount_currency, currency, move_date, account_1=None, partner=None):
        write_off_account_to_be_reconciled = account_1 if account_1 else self.receivable_account
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'date': move_date,
            'line_ids': [
                Command.create({
                    'debit': balance if balance > 0.0 else 0.0,
                    'credit': -balance if balance < 0.0 else 0.0,
                    'amount_currency': amount_currency,
                    'account_id': write_off_account_to_be_reconciled.id,
                    'currency_id': currency.id,
                    'partner_id': partner.id if partner else None,
                }),
                Command.create({
                    'debit': -balance if balance < 0.0 else 0.0,
                    'credit': balance if balance > 0.0 else 0.0,
                    'amount_currency': -amount_currency,
                    'account_id': self.company_data['default_account_revenue'].id,
                    'currency_id': currency.id,
                    'partner_id': partner.id if partner else None,
                }),
            ],
        })
        move.action_post()
        line = move.line_ids.filtered(lambda x: x.account_id == write_off_account_to_be_reconciled)

        self.assertRecordValues(line, [{
            'amount_residual': balance,
            'amount_residual_currency': amount_currency,
            'reconciled': False,
        }])

        return line
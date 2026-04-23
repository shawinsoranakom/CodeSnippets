def _create_exchange_difference_moves(self, exchange_diff_values_list):
        """ Create the exchange difference journal entry on the current journal items.

        :param exchange_diff_values_list:   A list of values to create and reconcile the exchange differences
                                            See the '_prepare_exchange_difference_move_vals' method.
        :return: An account.move recordset.
        """
        # early return to prevent endless recursive computation of reconcile plan
        if not exchange_diff_values_list:
            return self.env['account.move']

        exchange_move_values_list = []
        journal_ids = set()
        for exchange_diff_values in exchange_diff_values_list:
            move_vals = exchange_diff_values['move_values']
            exchange_move_values_list.append(move_vals)

            if not move_vals['journal_id']:
                raise UserError(_(
                    "You have to configure the 'Exchange Gain or Loss Journal' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))

            journal_ids.add(move_vals['journal_id'])

        # ==== Check the config ====
        journals = self.env['account.journal'].browse(list(journal_ids))
        for journal in journals:
            if not journal.company_id.expense_currency_exchange_account_id:
                raise UserError(_(
                    "You should configure the 'Loss Exchange Rate Account' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))
            if not journal.company_id.income_currency_exchange_account_id.id:
                raise UserError(_(
                    "You should configure the 'Gain Exchange Rate Account' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))

        # ==== Create the moves ====
        exchange_moves = self.env['account.move'].with_context(no_exchange_difference=True).create(exchange_move_values_list)
        # The reconciliation of exchange moves is now dealt thanks to the reconciled_lines_ids field

        # ==== See if the exchange moves need to be posted or not ====
        exchange_moves_to_post = self.env['account.move']
        for exchange_move, vals in zip(exchange_moves, exchange_diff_values_list):
            if vals['to_post']:
                exchange_moves_to_post |= exchange_move

        if exchange_moves_to_post:
            exchange_moves_to_post.with_context(validate_analytic=False)._post(soft=False)

        return exchange_moves
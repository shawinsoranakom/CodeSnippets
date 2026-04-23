def _create_tax_cash_basis_moves(self):
        ''' Create the tax cash basis journal entries.
        :return: The newly created journal entries.
        '''
        tax_cash_basis_values_per_move = self._collect_tax_cash_basis_values()
        today = fields.Date.context_today(self)

        moves_to_create_and_post = []
        moves_to_create_in_draft = []
        to_reconcile_after = []
        for move_values in tax_cash_basis_values_per_move.values():
            move = move_values['move']
            pending_cash_basis_lines = []
            amount_residual_per_tax_line = {line.id: line.amount_residual_currency for line_type, line in move_values['to_process_lines'] if line_type == 'tax'}

            for partial_values in move_values['partials']:
                partial = partial_values['partial']

                # Init the journal entry.
                journal = partial.company_id.tax_cash_basis_journal_id
                lock_date = move.company_id._get_user_fiscal_lock_date(journal)
                move_date = partial.max_date if partial.max_date > lock_date else today
                move_vals = {
                    'move_type': 'entry',
                    'date': move_date,
                    'ref': move.name,
                    'journal_id': journal.id,
                    'company_id': partial.company_id.id,
                    'line_ids': [],
                    'tax_cash_basis_rec_id': partial.id,
                    'tax_cash_basis_origin_move_id': move.id,
                    'fiscal_position_id': move.fiscal_position_id.id,
                }

                # Tracking of lines grouped all together.
                # Used to reduce the number of generated lines and to avoid rounding issues.
                partial_lines_to_create = {}

                for caba_treatment, line in move_values['to_process_lines']:
                    # ==========================================================================
                    # Compute the balance of the current line on the cash basis entry.
                    # This balance is a percentage representing the part of the journal entry
                    # that is actually paid by the current partial.
                    # ==========================================================================

                    # Percentage expressed in the foreign currency.
                    amount_currency = line.currency_id.round(line.amount_currency * partial_values['percentage'])
                    if (
                        caba_treatment == 'tax'
                        and (
                            move_values['is_fully_paid']
                            or line.currency_id.compare_amounts(abs(line.amount_residual_currency), abs(amount_currency)) < 0
                        )
                        and partial_values == move_values['partials'][-1]
                    ):
                        # If the move is supposed to be fully paid, and we're on the last partial for it,
                        # put the remaining amount to avoid rounding issues
                        amount_currency = amount_residual_per_tax_line[line.id]
                    if caba_treatment == 'tax':
                        amount_residual_per_tax_line[line.id] -= amount_currency
                    balance = partial_values['payment_rate'] and amount_currency / partial_values['payment_rate'] or 0.0

                    # ==========================================================================
                    # Prepare the mirror cash basis journal item of the current line.
                    # Group them all together as much as possible to reduce the number of
                    # generated journal items.
                    # Also track the computed balance in order to avoid rounding issues when
                    # the journal entry will be fully paid. At that case, we expect the exact
                    # amount of each line has been covered by the cash basis journal entries
                    # and well reported in the Tax Report.
                    # ==========================================================================

                    if caba_treatment == 'tax':
                        # Tax line.

                        cb_line_vals = self._prepare_cash_basis_tax_line_vals(line, balance, amount_currency)
                        grouping_key = self._get_cash_basis_tax_line_grouping_key_from_vals(cb_line_vals)
                    elif caba_treatment == 'base':
                        # Base line.

                        cb_line_vals = self._prepare_cash_basis_base_line_vals(line, balance, amount_currency)
                        cb_line_vals['name'] = ' - '.join(filter(None, (line.move_id.name, partial_values['counterpart_move'].name)))

                        grouping_key = self._get_cash_basis_base_line_grouping_key_from_vals(cb_line_vals)

                    if grouping_key in partial_lines_to_create:
                        aggregated_vals = partial_lines_to_create[grouping_key]['vals']

                        debit = aggregated_vals['debit'] + cb_line_vals['debit']
                        credit = aggregated_vals['credit'] + cb_line_vals['credit']
                        balance = debit - credit

                        aggregated_vals.update({
                            'debit': balance if balance > 0 else 0,
                            'credit': -balance if balance < 0 else 0,
                            'amount_currency': aggregated_vals['amount_currency'] + cb_line_vals['amount_currency'],
                        })

                        if caba_treatment == 'tax':
                            aggregated_vals.update({
                                'tax_base_amount': aggregated_vals['tax_base_amount'] + cb_line_vals['tax_base_amount'],
                            })
                            partial_lines_to_create[grouping_key]['tax_line'] += line
                    else:
                        partial_lines_to_create[grouping_key] = {
                            'vals': cb_line_vals,
                        }
                        if caba_treatment == 'tax':
                            partial_lines_to_create[grouping_key].update({
                                'tax_line': line,
                            })

                # ==========================================================================
                # Create the counterpart journal items.
                # ==========================================================================

                # To be able to retrieve the correct matching between the tax lines to reconcile
                # later, the lines will be created using a specific sequence.
                sequence = 0

                for grouping_key, aggregated_vals in partial_lines_to_create.items():
                    line_vals = aggregated_vals['vals']
                    line_vals['sequence'] = sequence

                    pending_cash_basis_lines.append((grouping_key, line_vals['amount_currency']))

                    if 'tax_repartition_line_id' in line_vals:
                        # Tax line.

                        tax_line = aggregated_vals['tax_line']
                        counterpart_line_vals = self._prepare_cash_basis_counterpart_tax_line_vals(tax_line, line_vals)
                        counterpart_line_vals['sequence'] = sequence + 1

                        if tax_line.account_id.reconcile:
                            move_index = len(moves_to_create_and_post) + len(moves_to_create_in_draft)
                            to_reconcile_after.append((tax_line, move_index, counterpart_line_vals['sequence']))

                    else:
                        # Base line.

                        counterpart_line_vals = self._prepare_cash_basis_counterpart_base_line_vals(line_vals)
                        counterpart_line_vals['sequence'] = sequence + 1

                    sequence += 2

                    move_vals['line_ids'] += [(0, 0, counterpart_line_vals), (0, 0, line_vals)]

                if partial_values['both_move_posted']:
                    moves_to_create_and_post.append(move_vals)
                else:
                    moves_to_create_in_draft.append(move_vals)

        moves = self.env['account.move'].with_context(
            skip_invoice_sync=True,
            skip_invoice_line_sync=True,
            skip_account_move_synchronization=True,
        ).create(moves_to_create_and_post + moves_to_create_in_draft)
        moves[:len(moves_to_create_and_post)]._post(soft=False)

        # Reconcile the tax lines being on a reconcile tax basis transfer account.
        reconciliation_plan = []
        for lines, move_index, sequence in to_reconcile_after:

            # In expenses, all move lines are created manually without any grouping on tax lines.
            # In that case, 'lines' could be already reconciled.
            lines = lines.filtered(lambda x: not x.reconciled)
            if not lines:
                continue

            counterpart_line = moves[move_index].line_ids.filtered(lambda line: line.sequence == sequence)

            # When dealing with tiny amounts, the line could have a zero amount and then, be already reconciled.
            if counterpart_line.reconciled:
                continue

            reconciliation_plan.append((counterpart_line + lines))

        # passing add_caba_vals in the context to make sure that any exchange diff that would be created for
        # this cash basis move would set the field draft_caba_move_vals accordingly on the partial
        self.env['account.move.line'].with_context(add_caba_vals=True)._reconcile_plan(reconciliation_plan)
        return moves
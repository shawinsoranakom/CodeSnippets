def stream_initial_balance(self):
            with get_cursor() as cr:
                self = self.with_env(self.env(cr=cr))
                unaffected_earnings_account = self.env['account.account'].search([
                    *self.env['account.account']._check_company_domain(company),
                    ('account_type', '=', 'equity_unaffected'),
                ], order='code desc', limit=1)
                unaffected_earnings_line = True  # used to make sure that we add the unaffected earning initial balance only once
                if unaffected_earnings_account:
                    # compute the benefit/loss of last year to add in the initial balance of the current year earnings account
                    unaffected_earnings_results = self._do_query_unaffected_earnings()
                    unaffected_earnings_line = False

                query = self.env['account.move.line']._search(self._get_base_domain() + [
                    ('date', '<', self.date_from),
                    ('account_id.include_initial_balance', '=', True),
                    ('account_id.account_type', 'not in', ['asset_receivable', 'liability_payable']),
                ])
                aa_code = self.env['account.account']._field_to_sql('account_move_line__account_id', 'code', query)
                sql_query = query.select(SQL(
                    """
                        'OUV' AS JournalCode,
                        'Balance initiale' AS JournalLib,
                        'OUVERTURE/' || %(formatted_date_year)s AS EcritureNum,
                        %(formatted_date_from)s AS EcritureDate,
                        MIN(%(aa_code)s) AS CompteNum,
                        replace(replace(MIN(%(aa_name)s), '|', '/'), '\t', '') AS CompteLib,
                        '' AS CompAuxNum,
                        '' AS CompAuxLib,
                        '-' AS PieceRef,
                        %(formatted_date_from)s AS PieceDate,
                        '/' AS EcritureLib,
                        replace(CASE WHEN sum(account_move_line.balance) <= 0 THEN '0,00' ELSE to_char(SUM(account_move_line.balance), '000000000000000D99') END, '.', ',') AS Debit,
                        replace(CASE WHEN sum(account_move_line.balance) >= 0 THEN '0,00' ELSE to_char(-SUM(account_move_line.balance), '000000000000000D99') END, '.', ',') AS Credit,
                        '' AS EcritureLet,
                        '' AS DateLet,
                        %(formatted_date_from)s AS ValidDate,
                        '' AS Montantdevise,
                        '' AS Idevise,
                        MIN(account_move_line__account_id.id) AS CompteID
                    """,
                    formatted_date_year=self.date_from.year,
                    formatted_date_from=fields.Date.to_string(self.date_from).replace('-', ''),
                    aa_code=aa_code,
                    aa_name=aa_name,
                ))
                self.env.cr.execute(SQL('%s GROUP BY account_move_line__account_id.id', sql_query))

                currency_digits = 2
                for row in self.env.cr.fetchall():
                    listrow = list(row)
                    account_id = listrow.pop()
                    if not unaffected_earnings_line:
                        account = self.env['account.account'].browse(account_id)
                        if account.account_type == 'equity_unaffected':
                            # add the benefit/loss of previous fiscal year to the first unaffected earnings account found.
                            unaffected_earnings_line = True
                            current_amount = float(listrow[11].replace(',', '.')) - float(listrow[12].replace(',', '.'))
                            unaffected_earnings_amount = float(unaffected_earnings_results[11].replace(',', '.')) - float(unaffected_earnings_results[12].replace(',', '.'))
                            listrow_amount = current_amount + unaffected_earnings_amount
                            if float_is_zero(listrow_amount, precision_digits=currency_digits):
                                continue
                            if listrow_amount > 0:
                                listrow[11] = str(listrow_amount).replace('.', ',')
                                listrow[12] = '0,00'
                            else:
                                listrow[11] = '0,00'
                                listrow[12] = str(-listrow_amount).replace('.', ',')
                    yield format_row(listrow)

                # if the unaffected earnings account wasn't in the selection yet: add it manually
                if (not unaffected_earnings_line
                    and unaffected_earnings_results
                    and (unaffected_earnings_results[11] != '0,00'
                        or unaffected_earnings_results[12] != '0,00')):
                    # search an unaffected earnings account
                    unaffected_earnings_account = self.env['account.account'].search([
                        ('account_type', '=', 'equity_unaffected')
                    ], order='code desc', limit=1)
                    if unaffected_earnings_account:
                        unaffected_earnings_results[4] = unaffected_earnings_account.code
                        unaffected_earnings_results[5] = unaffected_earnings_account.name
                    yield format_row(unaffected_earnings_results)

                # INITIAL BALANCE - receivable/payable
                query = self.env['account.move.line']._search(self._get_base_domain() + [
                    ('date', '<', self.date_from),
                    ('account_id.include_initial_balance', '=', True),
                    ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
                ])
                query.left_join('account_move_line', 'partner_id', 'res_partner', 'id', 'partner_id')
                aa_code = self.env['account.account']._field_to_sql('account_move_line__account_id', 'code', query)
                sql_query = query.select(SQL(
                    """
                        'OUV' AS JournalCode,
                        'Balance initiale' AS JournalLib,
                        'OUVERTURE/' || %(formatted_date_year)s AS EcritureNum,
                        %(formatted_date_from)s AS EcritureDate,
                        MIN(%(aa_code)s) AS CompteNum,
                        replace(MIN(%(aa_name)s), '|', '/') AS CompteLib,
                        COALESCE(NULLIF(replace(account_move_line__partner_id.ref, '|', '/'), ''), account_move_line__partner_id.id::text) AS CompAuxNum,
                        COALESCE(replace(account_move_line__partner_id.name, '|', '/'), '') AS CompAuxLib,
                        '-' AS PieceRef,
                        %(formatted_date_from)s AS PieceDate,
                        '/' AS EcritureLib,
                        replace(CASE WHEN sum(account_move_line.balance) <= 0 THEN '0,00' ELSE to_char(SUM(account_move_line.balance), '000000000000000D99') END, '.', ',') AS Debit,
                        replace(CASE WHEN sum(account_move_line.balance) >= 0 THEN '0,00' ELSE to_char(-SUM(account_move_line.balance), '000000000000000D99') END, '.', ',') AS Credit,
                        '' AS EcritureLet,
                        '' AS DateLet,
                        %(formatted_date_from)s AS ValidDate,
                        '' AS Montantdevise,
                        '' AS Idevise,
                        MIN(account_move_line__account_id.id) AS CompteID
                    """,
                    formatted_date_year=self.date_from.year,
                    formatted_date_from=fields.Date.to_string(self.date_from).replace('-', ''),
                    aa_code=aa_code,
                    aa_name=aa_name,
                ))
                self.env.cr.execute(SQL('%s GROUP BY account_move_line__partner_id.id, account_move_line__account_id.id', sql_query))

                for row in self.env.cr.fetchall():
                    listrow = list(row)
                    listrow.pop()
                    yield format_row(listrow)
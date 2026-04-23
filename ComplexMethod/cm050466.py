def _prepare_aml_values_list_per_nature(self):
        AccountTax = self.env['account.tax']
        sign = 1 if self.amount_total < 0 else -1
        commercial_partner = self.partner_id.commercial_partner_id
        company_currency = self.company_id.currency_id
        rate = self.currency_id._get_conversion_rate(self.currency_id, company_currency, self.company_id, self.date_order)

        # Concert each order line to a dictionary containing business values. Also, prepare for taxes computation.
        base_lines = self._prepare_tax_base_line_values()
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id)
        AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines, self.company_id)
        tax_results = AccountTax._prepare_tax_lines(base_lines, self.company_id)

        total_balance = 0.0
        total_amount_currency = 0.0
        aml_vals_list_per_nature = defaultdict(list)

        # Create the tax lines
        for tax_line in tax_results['tax_lines_to_add']:
            aml_vals_list_per_nature['tax'].append({
                **tax_line,
                'display_type': 'tax',
            })
            total_amount_currency += tax_line['amount_currency']
            total_balance += tax_line['balance']

        # Create the aml values for order lines.
        for base_line_vals, update_base_line_vals in tax_results['base_lines_to_update']:
            product_dict = self._prepare_product_aml_dict(base_line_vals, update_base_line_vals, rate, sign)
            aml_vals_list_per_nature['product'].append(product_dict)
            total_amount_currency += product_dict['amount_currency']
            total_balance += product_dict['balance']

        # Cash rounding.
        cash_rounding = self.config_id.rounding_method
        if self.config_id.cash_rounding and cash_rounding and (not self.config_id.only_round_cash_method or any(p.payment_method_id.is_cash_count for p in self.payment_ids)):
            if self.config_id.only_round_cash_method and any(not p.payment_method_id.is_cash_count for p in self.payment_ids):
                # If only_round_cash_method is True, and there are non-cash payments, cash rounding must be computed
                # based on the total amount of the order, and total payment amount.
                total_payment_amount = self.currency_id.round(sum(p.amount for p in self.payment_ids))
                amount_currency = sign * self.currency_id.round(self.currency_id.round(total_amount_currency) + total_payment_amount)
            else:
                amount_currency = cash_rounding.compute_difference(self.currency_id, total_amount_currency)
            if not self.currency_id.is_zero(amount_currency):
                balance = company_currency.round(amount_currency * rate)

                if cash_rounding.strategy == 'biggest_tax':
                    biggest_tax_aml_vals = None
                    for aml_vals in aml_vals_list_per_nature['tax']:
                        if not biggest_tax_aml_vals or float_compare(-sign * aml_vals['amount_currency'], -sign * biggest_tax_aml_vals['amount_currency'], precision_rounding=self.currency_id.rounding) > 0:
                            biggest_tax_aml_vals = aml_vals
                    if biggest_tax_aml_vals:
                        biggest_tax_aml_vals['amount_currency'] += amount_currency
                        biggest_tax_aml_vals['balance'] += balance
                elif cash_rounding.strategy == 'add_invoice_line':
                    if -sign * amount_currency > 0.0 and cash_rounding.loss_account_id:
                        account_id = cash_rounding.loss_account_id.id
                    else:
                        account_id = cash_rounding.profit_account_id.id
                    aml_vals_list_per_nature['cash_rounding'].append({
                        'name': cash_rounding.name,
                        'account_id': account_id,
                        'partner_id': commercial_partner.id,
                        'currency_id': self.currency_id.id,
                        'amount_currency': amount_currency,
                        'balance': balance,
                        'display_type': 'rounding',
                    })
        # Stock.
        if self.picking_ids.ids:
            stock_moves = self.env['stock.move'].sudo().search([
                ('picking_id', 'in', self.picking_ids.ids),
                ('product_id.valuation', '=', 'real_time'),
            ])
            for stock_move in stock_moves:
                product_accounts = stock_move.with_company(stock_move.company_id).product_id._get_product_accounts()
                expense_account = product_accounts['expense']
                stock_account = product_accounts['stock_valuation']
                balance = stock_move.value if stock_move.is_out else -stock_move.value
                aml_vals_list_per_nature['stock'].append({
                    'name': _("Stock variation for %s", stock_move.product_id.name),
                    'account_id': expense_account.id,
                    'partner_id': commercial_partner.id,
                    'currency_id': self.company_id.currency_id.id,
                    'amount_currency': balance,
                    'balance': balance,
                })
                aml_vals_list_per_nature['stock'].append({
                    'name': _("Stock variation for %s", stock_move.product_id.name),
                    'account_id': stock_account.id,
                    'partner_id': commercial_partner.id,
                    'currency_id': self.company_id.currency_id.id,
                    'amount_currency': -balance,
                    'balance': -balance,
                })

        # sort self.payment_ids by is_split_transaction:
        for payment_id in self.payment_ids:
            is_split_transaction = payment_id.payment_method_id.split_transactions
            if is_split_transaction:
                reversed_move_receivable_account_id = self.partner_id.property_account_receivable_id
            else:
                reversed_move_receivable_account_id = payment_id.payment_method_id.receivable_account_id or self.company_id.account_default_pos_receivable_account_id

            aml_vals_entry_found = [aml_entry for aml_entry in aml_vals_list_per_nature['payment_terms']
                                    if aml_entry['account_id'] == reversed_move_receivable_account_id.id
                                    and not aml_entry['partner_id']]

            if aml_vals_entry_found and not is_split_transaction:
                aml_vals_entry_found[0]['amount_currency'] += self.session_id._amount_converter(payment_id.amount, self.date_order, False)
                aml_vals_entry_found[0]['balance'] += payment_id.amount
            else:
                aml_vals_list_per_nature['payment_terms'].append({
                    'partner_id': commercial_partner.id if is_split_transaction else False,
                    'name': f"{reversed_move_receivable_account_id.code} {reversed_move_receivable_account_id.code}",
                    'account_id': reversed_move_receivable_account_id.id,
                    'currency_id': self.currency_id.id,
                    'amount_currency': payment_id.amount,
                    'balance': self.session_id._amount_converter(payment_id.amount, self.date_order, False),
                    'display_type': 'payment_term',
                })

        return aml_vals_list_per_nature
def _accumulate_amounts(self, data):
        # Accumulate the amounts for each accounting lines group
        # Each dict maps `key` -> `amounts`, where `key` is the group key.
        # E.g. `combine_receivables_bank` is derived from pos.payment records
        # in the self.order_ids with group key of the `payment_method_id`
        # field of the pos.payment record.
        AccountTax = self.env['account.tax']
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
        tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
        split_receivables_bank = defaultdict(amounts)
        split_receivables_cash = defaultdict(amounts)
        split_receivables_pay_later = defaultdict(amounts)
        combine_receivables_bank = defaultdict(amounts)
        combine_receivables_cash = defaultdict(amounts)
        combine_receivables_pay_later = defaultdict(amounts)
        combine_invoice_receivables = defaultdict(amounts)
        split_invoice_receivables = defaultdict(amounts)
        sales = defaultdict(amounts)
        taxes = defaultdict(tax_amounts)
        stock_expense = defaultdict(amounts)
        stock_return = defaultdict(amounts)
        stock_valuation = defaultdict(amounts)
        rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
        # Track the receivable lines of the order's invoice payment moves for reconciliation
        # These receivable lines are reconciled to the corresponding invoice receivable lines
        # of this session's move_id.
        combine_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        split_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        pos_receivable_account = self.company_id.account_default_pos_receivable_account_id
        currency_rounding = self.currency_id.rounding
        closed_orders = self._get_closed_orders()
        for order in closed_orders:
            order_is_invoiced = order.is_invoiced
            for payment in order.payment_ids:
                amount = payment.amount
                if float_is_zero(amount, precision_rounding=currency_rounding):
                    continue
                date = payment.payment_date
                payment_method = payment.payment_method_id
                is_split_payment = payment.payment_method_id.split_transactions
                payment_type = payment_method.type

                # If not pay_later, we create the receivable vals for both invoiced and uninvoiced orders.
                #   Separate the split and aggregated payments.
                # Moreover, if the order is invoiced, we create the pos receivable vals that will balance the
                # pos receivable lines from the invoice payments.
                if payment_type != 'pay_later':
                    if is_split_payment and payment_type == 'cash':
                        split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'cash':
                        combine_receivables_cash[payment_method] = self._update_amounts(combine_receivables_cash[payment_method], {'amount': amount}, date)
                    elif is_split_payment and payment_type == 'bank':
                        split_receivables_bank[payment] = self._update_amounts(split_receivables_bank[payment], {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'bank':
                        combine_receivables_bank[payment_method] = self._update_amounts(combine_receivables_bank[payment_method], {'amount': amount}, date)

                    # Create the vals to create the pos receivables that will balance the pos receivables from invoice payment moves.
                    if order_is_invoiced:
                        if is_split_payment:
                            split_inv_payment_receivable_lines[payment] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            split_invoice_receivables[payment] = self._update_amounts(split_invoice_receivables[payment], {'amount': payment.amount}, order.date_order)
                        else:
                            combine_inv_payment_receivable_lines[payment_method] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            combine_invoice_receivables[payment_method] = self._update_amounts(combine_invoice_receivables[payment_method], {'amount': payment.amount}, order.date_order)

                # If pay_later, we create the receivable lines.
                #   if split, with partner
                #   Otherwise, it's aggregated (combined)
                # But only do if order is *not* invoiced because no account move is created for pay later invoice payments.
                if payment_type == 'pay_later' and not order_is_invoiced:
                    if is_split_payment:
                        split_receivables_pay_later[payment] = self._update_amounts(split_receivables_pay_later[payment], {'amount': amount}, date)
                    elif not is_split_payment:
                        combine_receivables_pay_later[payment_method] = self._update_amounts(combine_receivables_pay_later[payment_method], {'amount': amount}, date)

            if not order_is_invoiced:
                base_lines = order.with_context(linked_to_pos=True)._prepare_tax_base_line_values()
                AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
                AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
                AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines, order.company_id, include_caba_tags=True)
                tax_results = AccountTax._prepare_tax_lines(base_lines, order.company_id)
                total_amount_currency = 0.0
                for base_line, to_update in tax_results['base_lines_to_update']:
                    # Combine sales/refund lines
                    sale_vals_dict = self._get_sale_key(base_line)
                    sale_key = frozendict(sale_vals_dict)
                    total_amount_currency += to_update['amount_currency']
                    sales[sale_key] = self._update_amounts(
                        sales[sale_key],
                        {
                            'amount': to_update['amount_currency'],
                            'amount_converted': to_update['balance'],
                        },
                        order.date_order,
                    )
                    if self.config_id._is_quantities_set():
                        sales[sale_key].setdefault('quantity', 0)
                        sales[sale_key]['quantity'] += base_line['quantity']

                # Combine tax lines
                for tax_line in tax_results['tax_lines_to_add']:
                    tax_key = (
                        tax_line['account_id'],
                        tax_line['tax_repartition_line_id'],
                        tuple(tax_line['tax_tag_ids'][0][2]),
                    )
                    total_amount_currency += tax_line['amount_currency']
                    taxes[tax_key] = self._update_amounts(
                        taxes[tax_key],
                        {
                            'amount': tax_line['amount_currency'],
                            'amount_converted': tax_line['balance'],
                            'base_amount': tax_line['tax_base_amount']
                        },
                        order.date_order,
                    )

                if self.config_id.cash_rounding:
                    diff = order.amount_paid + total_amount_currency
                    rounding_difference = self._update_amounts(rounding_difference, {'amount': diff}, order.date_order)

                # Increasing current partner's customer_rank
                partners = (order.partner_id | order.partner_id.commercial_partner_id)
                partners._increase_rank('customer_rank')

        all_picking_ids = self.order_ids.filtered(lambda p: not p.is_invoiced and not p.shipping_date).picking_ids.ids + self.picking_ids.filtered(lambda p: not p.pos_order_id).ids
        if all_picking_ids:
            # Combine stock lines
            stock_move_sudo = self.env['stock.move'].sudo()
            stock_moves = stock_move_sudo.search([
                ('picking_id', 'in', all_picking_ids),
                ('product_id.is_storable', '=', True),
                ('product_id.valuation', '=', 'real_time'),
            ])
            for stock_moves_batch in split_every(PREFETCH_MAX, stock_moves._ids, stock_moves.browse):
                for move in stock_moves_batch:
                    product_accounts = move.product_id._get_product_accounts()
                    exp_key = product_accounts['expense']
                    stock_key = product_accounts['stock_valuation']
                    signed_product_qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id, round=False)
                    if move._is_in():
                        signed_product_qty *= -1
                    amount = signed_product_qty * move._get_price_unit()
                    stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date_done, force_company_currency=True)
                    if move._is_in():
                        stock_return[stock_key] = self._update_amounts(stock_return[stock_key], {'amount': amount}, move.picking_id.date_done, force_company_currency=True)
                    else:
                        stock_valuation[stock_key] = self._update_amounts(stock_valuation[stock_key], {'amount': amount}, move.picking_id.date_done, force_company_currency=True)

        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False, skip_invoice_sync=True)

        data.update({
            'taxes':                               taxes,
            'sales':                               sales,
            'stock_expense':                       stock_expense,
            'split_receivables_bank':              split_receivables_bank,
            'combine_receivables_bank':            combine_receivables_bank,
            'split_receivables_cash':              split_receivables_cash,
            'combine_receivables_cash':            combine_receivables_cash,
            'combine_invoice_receivables':         combine_invoice_receivables,
            'split_receivables_pay_later':         split_receivables_pay_later,
            'combine_receivables_pay_later':       combine_receivables_pay_later,
            'stock_return':                        stock_return,
            'stock_valuation':                     stock_valuation,
            'combine_inv_payment_receivable_lines': combine_inv_payment_receivable_lines,
            'rounding_difference':                 rounding_difference,
            'MoveLine':                            MoveLine,
            'split_invoice_receivables': split_invoice_receivables,
            'split_inv_payment_receivable_lines': split_inv_payment_receivable_lines,
        })
        return data
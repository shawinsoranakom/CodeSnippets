def _get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line(self):
        """ Helper to get the values to create the counterpart journal items on the register payment wizard and the
        bank reconciliation widget in case of an early payment discount. When the early payment discount computation
        is included, we need to compute the base amounts / tax amounts for each receivable / payable but we need to
        take care about the rounding issues. For others computations, we need to balance the discount you get.

        :return: A list of values to create the counterpart journal items split in 3 categories:
            * term_lines:   The journal items containing the discount amounts for each receivable line when the
                            discount computation is excluded / mixed.
            * tax_lines:    The journal items acting as tax lines when the discount computation is included.
            * base_lines:   The journal items acting as base for tax lines when the discount computation is included.
        """
        self.ensure_one()

        def inverse_tax_rep(tax_rep):
            tax = tax_rep.tax_id
            index = list(tax.invoice_repartition_line_ids).index(tax_rep)
            return tax.refund_repartition_line_ids[index]

        company = self.company_id
        payment_term_line = self.line_ids.filtered(lambda x: x.display_type == 'payment_term')
        tax_lines = self.line_ids.filtered('tax_repartition_line_id')
        invoice_lines = self.line_ids.filtered(lambda x: x.display_type == 'product')
        payment_term = self.invoice_payment_term_id
        early_pay_discount_computation = payment_term.early_pay_discount_computation
        discount_percentage = payment_term.discount_percentage

        res = {
            'term_lines': defaultdict(lambda: {}),
            'tax_lines': defaultdict(lambda: {}),
            'base_lines': defaultdict(lambda: {}),
        }
        if not discount_percentage:
            return res

        # Get the current tax amounts in the current invoice.
        tax_amounts = {
            inverse_tax_rep(line.tax_repartition_line_id).id: {
                'amount_currency': line.amount_currency,
                'balance': line.balance,
            }
            for line in tax_lines
        }

        base_lines = [
            {
                **self._prepare_product_base_line_for_taxes_computation(line),
                'is_refund': True,
            }
            for line in invoice_lines
        ]
        for base_line in base_lines:
            base_line['tax_ids'] = base_line['tax_ids'].filtered(lambda t: t.amount_type != 'fixed')

            if early_pay_discount_computation == 'included':
                remaining_part_to_consider = (100 - discount_percentage) / 100.0
                base_line['price_unit'] *= remaining_part_to_consider
        AccountTax = self.env['account.tax']
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id)
        AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines, self.company_id)

        if self.is_inbound(include_receipts=True):
            cash_discount_account = company.account_journal_early_pay_discount_loss_account_id
        else:
            cash_discount_account = company.account_journal_early_pay_discount_gain_account_id

        epd_analytic_distribution = self.env['account.analytic.distribution.model']._get_distribution({
            'account_prefix': cash_discount_account.code,
            'company_id': self.company_id.id,
            'partner_id': self.commercial_partner_id.id,
            'partner_category_id': self.partner_id.category_id.ids,
        })

        bases_details = {}

        term_amount_currency = payment_term_line.amount_currency - payment_term_line.discount_amount_currency
        term_balance = payment_term_line.balance - payment_term_line.discount_balance
        if early_pay_discount_computation == 'included' and invoice_lines.tax_ids:
            # Compute the base amounts.
            resulting_delta_base_details = {}
            resulting_delta_tax_details = {}
            for base_line in base_lines:
                tax_details = base_line['tax_details']
                invoice_line = base_line['record']

                grouping_dict = {
                    'tax_ids': [Command.set(base_line['tax_ids'].ids)],
                    'tax_tag_ids': [Command.set(base_line['tax_tag_ids'].ids)],
                    'partner_id': base_line['partner_id'].id,
                    'currency_id': base_line['currency_id'].id,
                    'account_id': cash_discount_account.id,
                    'analytic_distribution': base_line['analytic_distribution'] or epd_analytic_distribution,
                }
                base_detail = resulting_delta_base_details.setdefault(frozendict(grouping_dict), {
                    'balance': 0.0,
                    'amount_currency': 0.0,
                })

                amount_currency = self.currency_id\
                    .round(self.direction_sign * tax_details['total_excluded_currency'] - invoice_line.amount_currency)
                balance = self.company_currency_id\
                    .round(self.direction_sign * tax_details['total_excluded'] - invoice_line.balance)

                base_detail['balance'] += balance
                base_detail['amount_currency'] += amount_currency

                bases_details[frozendict(grouping_dict)] = base_detail

            # Compute the tax amounts.
            tax_results = AccountTax._prepare_tax_lines(base_lines, self.company_id)
            for tax_line_vals in tax_results['tax_lines_to_add']:
                tax_amount_without_epd = tax_amounts.get(tax_line_vals['tax_repartition_line_id'])
                if tax_amount_without_epd:
                    resulting_delta_tax_details[tax_line_vals['tax_repartition_line_id']] = {
                        **tax_line_vals,
                        'amount_currency': tax_line_vals['amount_currency'] - tax_amount_without_epd['amount_currency'],
                        'balance': tax_line_vals['balance'] - tax_amount_without_epd['balance'],
                    }

            # Multiply the amount by the percentage
            percentage_paid = abs(payment_term_line.amount_residual_currency / self.amount_total)
            for tax_line_vals in resulting_delta_tax_details.values():
                tax_rep = self.env['account.tax.repartition.line'].browse(tax_line_vals['tax_repartition_line_id'])
                tax = tax_rep.tax_id

                grouping_dict = {
                    'account_id': tax_line_vals['account_id'],
                    'partner_id': tax_line_vals['partner_id'],
                    'currency_id': tax_line_vals['currency_id'],
                    'analytic_distribution': tax_line_vals['analytic_distribution'],
                    'tax_repartition_line_id': tax_rep.id,
                    'tax_ids': tax_line_vals['tax_ids'],
                    'tax_tag_ids': tax_line_vals['tax_tag_ids'],
                    'group_tax_id': tax_line_vals['group_tax_id'],
                }

                res['tax_lines'][payment_term_line][frozendict(grouping_dict)] = {
                    'name': _("Early Payment Discount (%s)", tax.name),
                    'amount_currency': payment_term_line.currency_id.round(tax_line_vals['amount_currency'] * percentage_paid),
                    'balance': payment_term_line.company_currency_id.round(tax_line_vals['balance'] * percentage_paid),
                }

            for grouping_dict, base_detail in bases_details.items():
                res['base_lines'][payment_term_line][grouping_dict] = {
                    'name': _("Early Payment Discount"),
                    'amount_currency': payment_term_line.currency_id.round(base_detail['amount_currency'] * percentage_paid),
                    'balance': payment_term_line.company_currency_id.round(base_detail['balance'] * percentage_paid),
                }

            # Fix the rounding issue if any.
            delta_amount_currency = term_amount_currency \
                                    - sum(x['amount_currency'] for x in res['base_lines'][payment_term_line].values()) \
                                    - sum(x['amount_currency'] for x in res['tax_lines'][payment_term_line].values())
            delta_balance = term_balance \
                            - sum(x['balance'] for x in res['base_lines'][payment_term_line].values()) \
                            - sum(x['balance'] for x in res['tax_lines'][payment_term_line].values())

            biggest_base_line = max(list(res['base_lines'][payment_term_line].values()), key=lambda x: x['amount_currency'])
            biggest_base_line['amount_currency'] += delta_amount_currency
            biggest_base_line['balance'] += delta_balance

        else:
            grouping_dict = {'account_id': cash_discount_account.id}

            res['term_lines'][payment_term_line][frozendict(grouping_dict)] = {
                'name': _("Early Payment Discount"),
                'partner_id': payment_term_line.partner_id.id,
                'currency_id': payment_term_line.currency_id.id,
                'amount_currency': term_amount_currency,
                'balance': term_balance,
                'analytic_distribution': epd_analytic_distribution,
            }

        return res
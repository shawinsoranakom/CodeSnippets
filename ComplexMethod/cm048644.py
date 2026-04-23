def _get_rounded_base_and_tax_lines(self, round_from_tax_lines=True):
        """ Small helper to extract the base and tax lines for the taxes computation from the current move.
        The move could be stored or not and could have some features generating extra journal items acting as
        base lines for the taxes computation (e.g. epd, rounding lines).

        :param round_from_tax_lines:    Indicate if the manual tax amounts of tax journal items should be kept or not.
                                        It only works when the move is stored.
        :return:                        A tuple <base_lines, tax_lines> for the taxes computation.
        """
        self.ensure_one()
        AccountTax = self.env['account.tax']
        is_invoice = self.is_invoice(include_receipts=True)

        if self.id or not is_invoice:
            base_amls = self.line_ids.filtered(lambda line: line.display_type == 'product')
        else:
            base_amls = self.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
        base_lines = [self._prepare_product_base_line_for_taxes_computation(line) for line in base_amls]

        tax_lines = []
        if self.id:
            # The move is stored so we can add the early payment discount lines directly to reduce the
            # tax amount without touching the untaxed amount.
            epd_amls = self.line_ids.filtered(lambda line: line.display_type == 'epd')
            base_lines += [self._prepare_epd_base_line_for_taxes_computation(line) for line in epd_amls]
            cash_rounding_amls = self.line_ids \
                .filtered(lambda line: line.display_type == 'rounding' and not line.tax_repartition_line_id)
            base_lines += [self._prepare_cash_rounding_base_line_for_taxes_computation(line) for line in cash_rounding_amls]
            non_deductible_base_lines = self.line_ids.filtered(lambda line: line.display_type in ('non_deductible_product', 'non_deductible_product_total'))
            base_lines += [self._prepare_non_deductible_base_line_for_taxes_computation(line) for line in non_deductible_base_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
            tax_amls = self.line_ids.filtered('tax_repartition_line_id')
            tax_lines = [self._prepare_tax_line_for_taxes_computation(tax_line) for tax_line in tax_amls]
            if round_from_tax_lines == 'reapply_currency_rate':
                for tax_line in tax_lines:
                    rate = tax_line['record'].currency_rate
                    if rate:
                        tax_line['balance'] = self.company_currency_id.round(tax_line['amount_currency'] / rate)
            AccountTax._round_base_lines_tax_details(base_lines, self.company_id, tax_lines=tax_lines if round_from_tax_lines else [])
        else:
            # The move is not stored yet so the only thing we have is the invoice lines.
            base_lines += self._prepare_epd_base_lines_for_taxes_computation_from_base_lines(base_amls)
            base_lines += self._prepare_non_deductible_base_lines_for_taxes_computation_from_base_lines(base_amls)
            AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, self.company_id)
        return base_lines, tax_lines
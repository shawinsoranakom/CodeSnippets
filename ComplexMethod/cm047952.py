def _l10n_hu_edi_get_invoice_values(self):
        eu_country_codes = set(self.env.ref('base.europe').country_ids.mapped('code'))

        def get_vat_data(partner, force_vat=None):
            if partner.country_code == 'HU' or force_vat:
                return {
                    'tax_number': partner.l10n_hu_group_vat or (force_vat or partner.vat),
                    'group_member_tax_number': partner.l10n_hu_group_vat and (force_vat or partner.vat),
                }
            elif partner.country_code in eu_country_codes:
                return {'community_vat_number': partner.vat}
            else:
                return {'third_state_tax_id': partner.vat}

        def format_bank_account_number(bank_account):
            # Normalize IBANs (no spaces!)
            if bank_account.acc_type == 'iban':
                return normalize_iban(bank_account.acc_number)
            else:
                return bank_account.acc_number

        supplier = self.company_id.partner_id
        customer = self.partner_id.commercial_partner_id

        supplier_bank = self.partner_bank_id if self.partner_bank_id and self.move_type == "out_invoice" else supplier.bank_ids[:1]
        customer_bank = self.partner_bank_id if self.partner_bank_id and self.move_type == "out_refund" else customer.bank_ids[:1]

        currency_huf = self.env.ref('base.HUF')
        currency_rate = self._l10n_hu_get_currency_rate()

        base_invoice = self._l10n_hu_get_chain_base()

        invoice_values = {
            'invoice': self,
            'invoiceIssueDate': self.invoice_date,
            'completenessIndicator': False,
            'modifyWithoutMaster': False,
            'base_invoice': base_invoice if base_invoice != self else None,
            'supplier': supplier,
            'supplier_vat_data': get_vat_data(supplier, self.fiscal_position_id.foreign_vat),
            'supplierBankAccountNumber': format_bank_account_number(supplier_bank),
            'individualExemption': self.company_id.l10n_hu_tax_regime == 'ie',
            'customer': customer,
            'customerVatStatus': (not customer.is_company and 'PRIVATE_PERSON') or (customer.country_code == 'HU' and 'DOMESTIC') or 'OTHER',
            'customer_vat_data': get_vat_data(customer) if customer.is_company else None,
            'customerBankAccountNumber': format_bank_account_number(customer_bank),
            'smallBusinessIndicator': self.company_id.l10n_hu_tax_regime == 'sb',
            'exchangeRate': currency_rate,
            'cashAccountingIndicator': self.company_id.l10n_hu_tax_regime == 'ca',
            'shipping_partner': self.partner_shipping_id,
            'sales_partner': self.user_id,
            'mergedItemIndicator': False,
            'format_bool': format_bool,
            'float_repr': float_repr,
            'lines_values': [],
        }

        sign = 1.0 if self.is_inbound() else -1.0

        prev_chain_invoices = base_invoice._l10n_hu_get_chain_invoices().filtered(
            lambda m: m.l10n_hu_invoice_chain_index and m.l10n_hu_invoice_chain_index < self.l10n_hu_invoice_chain_index
        )
        first_line_number = sum(
            len(move.line_ids.filtered(lambda l: l.display_type in ['product', 'rounding']))
            for move in prev_chain_invoices
        ) + 1

        for (line_number, line) in enumerate(
            self.line_ids.filtered(lambda l: l.display_type in ['product', 'rounding']).sorted(lambda l: l.display_type),
            start=first_line_number,
        ):
            line_values = {
                'line': line,
                'lineNumber': line_number - first_line_number + 1,
                'lineNumberReference': base_invoice != self and line_number,
                'lineExpressionIndicator': line.product_id and line.product_uom_id,
                'lineNatureIndicator': {False: 'OTHER', 'service': 'SERVICE'}.get(line.product_id.type, 'PRODUCT'),
                'lineDescription': line.name.replace('\n', ' '),
            }

            if 'is_downpayment' in line and line.is_downpayment:
                # Advance and final invoices.
                line_values['advanceIndicator'] = True

                if not self._is_downpayment():
                    # This is a final invoice that deducts one or more advance invoices.
                    # In this case, we add a reference to the *last-paid* advance invoice (NAV only allows us to report one) if one exists,
                    # otherwise we don't add anything.

                    advance_invoices = line._get_downpayment_lines().mapped('move_id').filtered(lambda m: m.state == 'posted')
                    reconciled_moves = advance_invoices._get_reconciled_amls().move_id
                    last_reconciled_payment = reconciled_moves.filtered(lambda m: m.origin_payment_id or m.statement_line_id).sorted('date', reverse=True)[:1]

                    if last_reconciled_payment:
                        line_values.update({
                            'advanceOriginalInvoice': advance_invoices.filtered(lambda m: last_reconciled_payment in m._get_reconciled_amls().move_id)[0].name,
                            'advancePaymentDate': last_reconciled_payment.date,
                            'advanceExchangeRate': last_reconciled_payment._l10n_hu_get_currency_rate(),
                        })

            if line.display_type == 'product':
                vat_tax = line.tax_ids.filtered(lambda t: t.l10n_hu_tax_type)

                if line.quantity == 0.0 or line.discount == 100.0:
                    price_unit_signed = 0.0
                else:
                    price_unit_signed = sign * line.price_subtotal / (1 - line.discount / 100) / line.quantity

                price_net_signed = self.currency_id.round(price_unit_signed * line.quantity * (1 - line.discount / 100.0))
                discount_value_signed = self.currency_id.round(price_unit_signed * line.quantity - price_net_signed)
                price_total_signed = sign * line.price_total
                vat_amount_signed = self.currency_id.round(price_total_signed - price_net_signed)

                line_values.update({
                    'vat_tax': vat_tax,
                    'vatPercentage': float_round(vat_tax.amount / 100.0, 4),
                    'quantity': line.quantity,
                    'unitPrice': price_unit_signed,
                    'unitPriceHUF': currency_huf.round(price_unit_signed * currency_rate),
                    'discountValue': discount_value_signed,
                    'discountRate': line.discount / 100.0,
                    'lineNetAmount': price_net_signed,
                    'lineNetAmountHUF': currency_huf.round(price_net_signed * currency_rate),
                    'lineVatData': not self.currency_id.is_zero(vat_amount_signed),
                    'lineVatAmount': vat_amount_signed,
                    'lineVatAmountHUF': currency_huf.round(vat_amount_signed * currency_rate),
                    'lineGrossAmountNormal': price_total_signed,
                    'lineGrossAmountNormalHUF': currency_huf.round(price_total_signed * currency_rate),
                })

            elif line.display_type == 'rounding':
                atk_tax = self.env['account.tax'].search(
                    [
                        ('type_tax_use', '=', 'sale'),
                        ('l10n_hu_tax_type', '=', 'ATK'),
                        ('company_id', '=', self.company_id.id),
                    ],
                    limit=1,
                )
                if not atk_tax:
                    raise UserError(_('Please create a sales tax with type ATK (outside the scope of the VAT Act).'))

                amount_huf = line.balance if self.company_id.currency_id == currency_huf else currency_huf.round(line.amount_currency * currency_rate)
                line_values.update({
                    'vat_tax': atk_tax,
                    'vatPercentage': float_round(atk_tax.amount / 100.0, 4),
                    'quantity': 1.0,
                    'unitPrice': -line.amount_currency,
                    'unitPriceHUF': -amount_huf,
                    'lineNetAmount': -line.amount_currency,
                    'lineNetAmountHUF': -amount_huf,
                    'lineVatData': False,
                    'lineGrossAmountNormal': -line.amount_currency,
                    'lineGrossAmountNormalHUF': -amount_huf,
                })
            line_values['lineDescription'] = line_values['lineDescription'] or line.product_id.display_name
            invoice_values['lines_values'].append(line_values)

        is_company_huf = self.company_id.currency_id == currency_huf
        tax_amounts_by_tax = {
            line.tax_line_id: {
                'vatRateVatAmount': -line.amount_currency,
                'vatRateVatAmountHUF': -line.balance if is_company_huf else currency_huf.round(-line.amount_currency * currency_rate),
            }
            for line in self.line_ids.filtered(lambda l: l.tax_line_id.l10n_hu_tax_type)
        }

        invoice_values['tax_summary'] = [
            {
                'vat_tax': vat_tax,
                'vatPercentage': float_round(vat_tax.amount / 100.0, 4),
                'vatRateNetAmount': self.currency_id.round(sum(l['lineNetAmount'] for l in lines_values_by_tax)),
                'vatRateNetAmountHUF': currency_huf.round(sum(l['lineNetAmountHUF'] for l in lines_values_by_tax)),
                'vatRateVatAmount': tax_amounts_by_tax.get(vat_tax, {}).get('vatRateVatAmount', 0.0),
                'vatRateVatAmountHUF': tax_amounts_by_tax.get(vat_tax, {}).get('vatRateVatAmountHUF', 0.0),
            }
            for vat_tax, lines_values_by_tax in groupby(invoice_values['lines_values'], lambda l: l['vat_tax'])
        ]

        total_vat = self.currency_id.round(sum(tax_vals['vatRateVatAmount'] for tax_vals in invoice_values['tax_summary']))
        total_vat_huf = currency_huf.round(sum(tax_vals['vatRateVatAmountHUF'] for tax_vals in invoice_values['tax_summary']))

        total_gross = self.amount_total_in_currency_signed
        total_gross_huf = self.amount_total_signed if is_company_huf else currency_huf.round(self.amount_total_in_currency_signed * currency_rate)

        total_net = self.currency_id.round(total_gross - total_vat)
        total_net_huf = currency_huf.round(total_gross_huf - total_vat_huf)

        invoice_values.update({
            'invoiceNetAmount': total_net,
            'invoiceNetAmountHUF': total_net_huf,
            'invoiceVatAmount': total_vat,
            'invoiceVatAmountHUF': total_vat_huf,
            'invoiceGrossAmount': total_gross,
            'invoiceGrossAmountHUF': total_gross_huf,
        })

        return invoice_values
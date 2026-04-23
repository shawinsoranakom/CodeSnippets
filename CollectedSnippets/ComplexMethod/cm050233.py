def _create_payment(self, **extra_create_values):
        """Create an `account.payment` record for the current transaction.

        If the transaction is linked to some invoices, their reconciliation is done automatically.

        Note: self.ensure_one()

        :param dict extra_create_values: Optional extra create values
        :return: The created payment
        :rtype: recordset of `account.payment`
        """
        self.ensure_one()

        reference = f'{self.reference} - {self.provider_reference or ""}'

        payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids\
            .filtered(lambda l: l.payment_provider_id == self.provider_id)
        payment_values = {
            'amount': abs(self.amount),  # A tx may have a negative amount, but a payment must >= 0
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': self.provider_id.journal_id.id,
            'company_id': self.provider_id.company_id.id,
            'payment_method_line_id': payment_method_line.id,
            'payment_token_id': self.token_id.id,
            'payment_transaction_id': self.id,
            'memo': reference,
            'write_off_line_vals': [],
            'invoice_ids': self.invoice_ids,
            **extra_create_values,
        }

        for invoice in self.invoice_ids:
            if invoice.state != 'posted':
                continue
            next_payment_values = invoice._get_invoice_next_payment_values()
            if next_payment_values['installment_state'] == 'epd' and self.amount == next_payment_values['amount_due']:
                aml = next_payment_values['epd_line']
                epd_aml_values_list = [({
                    'aml': aml,
                    'amount_currency': -aml.amount_residual_currency,
                    'balance': -aml.balance,
                })]
                open_balance = next_payment_values['epd_discount_amount']
                early_payment_values = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
                for aml_values_list in early_payment_values.values():
                    if (aml_values_list):
                        aml_vl = aml_values_list[0]
                        aml_vl['partner_id'] = invoice.partner_id.id
                        payment_values['write_off_line_vals'] += [aml_vl]
                break

        payment_term_lines = self.invoice_ids.line_ids.filtered(lambda line: line.display_type == 'payment_term')
        if payment_term_lines:
            payment_values['destination_account_id'] = payment_term_lines[0].account_id.id

        payment = self.env['account.payment'].create(payment_values)
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment

        # Reconcile the payment with the source transaction's invoices in case of a partial capture.
        if self.operation == self.source_transaction_id.operation:
            invoices = self.source_transaction_id.invoice_ids
        else:
            invoices = self.invoice_ids
        invoices = invoices.filtered(lambda inv: inv.state != 'cancel')
        if invoices:
            invoices.filtered(lambda inv: inv.state == 'draft').action_post()

            (payment.move_id.line_ids + invoices.line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                and not line.reconciled
            ).reconcile()

        return payment
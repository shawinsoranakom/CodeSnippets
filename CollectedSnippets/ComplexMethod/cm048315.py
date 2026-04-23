def _l10n_vn_edi_add_general_invoice_information(self, json_values):
        """ General invoice information, such as the model number, invoice symbol, type, date of issues, ... """
        self.ensure_one()
        invoice_data = {
            'transactionUuid': str(uuid.uuid4()),
            'invoiceType': self.l10n_vn_edi_invoice_symbol.invoice_template_id.template_invoice_type,
            'templateCode': self.l10n_vn_edi_invoice_symbol.invoice_template_id.name,
            'invoiceSeries': self.l10n_vn_edi_invoice_symbol.name,
            # This timestamp is important as it is used to check the chronological order of Invoice Numbers.
            # Since this xml is generated upon posting, just like the invoice number, using now() should keep that order
            # correct in most case.
            'invoiceIssuedDate': self._l10n_vn_edi_format_date(self.l10n_vn_edi_issue_date),
            'currencyCode': self.currency_id.name,
            'adjustmentType': '1',  # 1 for original invoice, which is the case during first issuance.
            'paymentStatus': self.payment_state in {'in_payment', 'paid'},
            'cusGetInvoiceRight': True,  # Set to true, allowing the customer to see the invoice.
            'validation': 1,  # Set to 1, SInvoice will validate tax information while processing the invoice.
        }

        # When invoicing in a foreign currency, we need to provide the rate, or it will default to 1.
        if self.currency_id.name != 'VND':
            # Sinvoice only allow upto 2 decimal place for exchange rate
            exchange_rate = self.env['res.currency']._get_conversion_rate(
                from_currency=self.currency_id,
                to_currency=self.env.ref('base.VND'),
                company=self.company_id,
                date=self.invoice_date or self.date,
            )
            invoice_data['exchangeRate'] = float_repr(float_round(exchange_rate, 2), 2)

        adjustment_origin_invoice = None
        if self.move_type == 'out_refund':  # Credit note are used to adjust an existing invoice
            adjustment_origin_invoice = self.reversed_entry_id
        elif self.l10n_vn_edi_replacement_origin_id:  # 'Reverse and create invoice' is used to issue a replacement invoice
            adjustment_origin_invoice = self.l10n_vn_edi_replacement_origin_id

        if adjustment_origin_invoice:
            invoice_data.update({
                'adjustmentType': '5' if self.move_type == 'out_refund' else '3',  # Adjustment or replacement
                'adjustmentInvoiceType': self.l10n_vn_edi_adjustment_type or '',
                'originalInvoiceId': adjustment_origin_invoice.l10n_vn_edi_invoice_number,
                'originalInvoiceIssueDate': self._l10n_vn_edi_format_date(adjustment_origin_invoice.l10n_vn_edi_issue_date),
                'originalTemplateCode': adjustment_origin_invoice.l10n_vn_edi_invoice_symbol.invoice_template_id.name,
                'additionalReferenceDesc': self.l10n_vn_edi_agreement_document_name,
                'additionalReferenceDate': self._l10n_vn_edi_format_date(self.l10n_vn_edi_agreement_document_date),
            })

        json_values['generalInvoiceInfo'] = invoice_data
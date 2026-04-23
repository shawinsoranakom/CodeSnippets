def _import_fill_invoice(self, invoice, tree, qty_factor):
        logs = []
        invoice_values = {}
        if qty_factor == -1:
            logs.append(_("The invoice has been converted into a credit note and the quantities have been reverted."))
        role = "AccountingCustomer" if invoice.journal_id.type == 'sale' else "AccountingSupplier"
        partner, partner_logs = self._import_partner(invoice.company_id, **self._import_retrieve_partner_vals(tree, role))
        # Need to set partner before to compute bank and lines properly
        invoice.partner_id = partner.id
        invoice_values['currency_id'], currency_logs = self._import_currency(tree, './/{*}DocumentCurrencyCode')
        invoice_values['invoice_date'] = tree.findtext('./{*}IssueDate')
        invoice_values['invoice_date_due'] = self._find_value(('./cbc:DueDate', './/cbc:PaymentDueDate'), tree)
        # ==== partner_bank_id ====
        bank_detail_nodes = tree.findall('.//{*}PaymentMeans')
        bank_details = [bank_detail_node.findtext('{*}PayeeFinancialAccount/{*}ID') for bank_detail_node in bank_detail_nodes if bank_detail_node.findtext('{*}PayeeFinancialAccount/{*}ID')]
        if bank_details:
            self._import_partner_bank(invoice, bank_details)

        # ==== ref, invoice_origin, narration, payment_reference ====
        ref = tree.findtext('./{*}ID')
        if ref and invoice.is_sale_document(include_receipts=True) and invoice.quick_edit_mode:
            invoice_values['name'] = ref
        elif ref:
            invoice_values['ref'] = ref
        invoice_values['invoice_origin'] = (
            tree.findtext('./{*}OrderReference/{*}ID')
            or ' '.join([desc.text for desc in tree.findall('.//{*}Item/{*}Description') if desc.text])
            or None
        )
        invoice_values['narration'] = self._import_description(tree, xpaths=['./{*}Note', './{*}PaymentTerms/{*}Note'])
        invoice_values['payment_reference'] = tree.findtext('./{*}PaymentMeans/{*}PaymentID')

        # ==== Delivery ====
        delivery_date = tree.find('.//{*}Delivery/{*}ActualDeliveryDate')
        invoice.delivery_date = delivery_date is not None and delivery_date.text

        # ==== invoice_incoterm_id ====
        incoterm_code = tree.findtext('./{*}TransportExecutionTerms/{*}DeliveryTerms/{*}ID')
        if incoterm_code:
            incoterm = self.env['account.incoterms'].search([('code', '=', incoterm_code)], limit=1)
            if incoterm:
                invoice_values['invoice_incoterm_id'] = incoterm.id

        # ==== Document level AllowanceCharge, Prepaid Amounts, Invoice Lines, Payable Rounding Amount ====
        allowance_charges_line_vals, allowance_charges_logs = self._import_document_allowance_charges(tree, invoice, invoice.journal_id.type, qty_factor)
        logs += self._import_prepaid_amount(invoice, tree, './{*}LegalMonetaryTotal/{*}PrepaidAmount', qty_factor)
        line_tag = (
            'InvoiceLine'
            if invoice.move_type in ('in_invoice', 'out_invoice') or qty_factor == -1
            else 'CreditNoteLine'
        )
        invoice_line_vals, line_logs = self._import_lines(invoice, tree, './{*}' + line_tag, document_type=invoice.move_type, tax_type=invoice.journal_id.type, qty_factor=qty_factor)
        rounding_line_vals, rounding_logs = self._import_rounding_amount(invoice, tree, './{*}LegalMonetaryTotal/{*}PayableRoundingAmount', document_type=invoice.move_type, qty_factor=qty_factor)
        line_vals = allowance_charges_line_vals + invoice_line_vals + rounding_line_vals

        invoice_values = {
            **invoice_values,
            'invoice_line_ids': [Command.create(line_value) for line_value in line_vals],
        }
        invoice.write(invoice_values)
        logs += partner_logs + currency_logs + line_logs + allowance_charges_logs + rounding_logs
        return logs
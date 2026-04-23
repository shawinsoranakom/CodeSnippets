def _import_fill_invoice(self, invoice, tree, qty_factor):
        logs = []
        invoice_values = {}
        if qty_factor == -1:
            logs.append(_("The invoice has been converted into a credit note and the quantities have been reverted."))
        role = 'SellerTradeParty' if invoice.journal_id.type == 'purchase' else 'BuyerTradeParty'
        partner, partner_logs = self._import_partner(invoice.company_id, **self._import_retrieve_partner_vals(tree, role))
        # Need to set partner before to compute bank and lines properly
        invoice.partner_id = partner.id
        invoice_values['currency_id'], currency_logs = self._import_currency(tree, './/{*}InvoiceCurrencyCode')

        # ==== partner_bank_id ====
        bank_detail_nodes = tree.findall('.//{*}SpecifiedTradeSettlementPaymentMeans')
        bank_details = [
            bank_detail_node.findtext('{*}PayeePartyCreditorFinancialAccount/{*}IBANID')
            or bank_detail_node.findtext('{*}PayeePartyCreditorFinancialAccount/{*}ProprietaryID')
            for bank_detail_node in bank_detail_nodes
            if bank_detail_node.findtext('{*}PayeePartyCreditorFinancialAccount/{*}IBANID')
            or bank_detail_node.findtext('{*}PayeePartyCreditorFinancialAccount/{*}ProprietaryID')
        ]
        if bank_details:
            self._import_partner_bank(invoice, bank_details=bank_details)

        # ==== ref, invoice_origin, narration, payment_reference ====
        invoice_values['ref'] = tree.findtext('./{*}ExchangedDocument/{*}ID')
        invoice_values['invoice_origin'] = tree.findtext(
            './/{*}BuyerOrderReferencedDocument/{*}IssuerAssignedID'
        )
        invoice_values['narration'] = self._import_description(tree, xpaths=[
            './{*}ExchangedDocument/{*}IncludedNote/{*}Content',
            './/{*}SpecifiedTradePaymentTerms/{*}Description',
        ])
        invoice_values['payment_reference'] = tree.findtext(
            './{*}SupplyChainTradeTransaction/{*}ApplicableHeaderTradeSettlement/{*}PaymentReference'
        )

        # ==== invoice_date, invoice_date_due ====
        issue_date = tree.findtext('./{*}ExchangedDocument/{*}IssueDateTime/{*}DateTimeString')
        if issue_date:
            invoice_values['invoice_date'] = datetime.strptime(issue_date.strip(), DEFAULT_FACTURX_DATE_FORMAT)
        due_date = tree.findtext('.//{*}SpecifiedTradePaymentTerms/{*}DueDateDateTime/{*}DateTimeString')
        if due_date:
            invoice_values['invoice_date_due'] = datetime.strptime(due_date.strip(), DEFAULT_FACTURX_DATE_FORMAT)

        # ==== Document level AllowanceCharge, Prepaid Amounts, Invoice Lines ====
        allowance_charges_line_vals, allowance_charges_logs = self._import_document_allowance_charges(
            tree, invoice, invoice.journal_id.type, qty_factor,
        )
        logs += self._import_prepaid_amount(invoice, tree, './/{*}ApplicableHeaderTradeSettlement/{*}SpecifiedTradeSettlementHeaderMonetarySummation/{*}TotalPrepaidAmount', qty_factor)
        invoice_line_vals, line_logs = self._import_lines(invoice, tree, './{*}SupplyChainTradeTransaction/{*}IncludedSupplyChainTradeLineItem',
                                                          document_type=invoice.move_type, tax_type=invoice.journal_id.type, qty_factor=qty_factor)
        line_vals = allowance_charges_line_vals + invoice_line_vals

        invoice_values = {
            **invoice_values,
            'invoice_line_ids': [Command.create(line_value) for line_value in line_vals],
        }
        invoice.write(invoice_values)
        logs += partner_logs + currency_logs + line_logs + allowance_charges_logs
        return logs
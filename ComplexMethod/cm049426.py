def _import_invoice_facturae_invoice(self, invoice, partner, tree):
        logs = []

        # ==== move_type ====
        invoice_total = find_xml_value('.//InvoiceTotal', tree)
        is_refund = float(invoice_total) < 0 if invoice_total else False
        if is_refund:
            invoice.move_type = "in_refund" if invoice.move_type.startswith("in_") else "out_refund"
        ref_multiplier = -1.0 if is_refund else 1.0

        # ==== partner_id ====
        if partner:
            invoice.partner_id = partner
        else:
            logs.append(_("Customer/Vendor could not be found and could not be created due to missing data in the XML."))

        # ==== currency_id ====
        invoice_currency_code = find_xml_value('.//InvoiceCurrencyCode', tree)
        if invoice_currency_code:
            currency = self.env['res.currency'].search([('name', '=', invoice_currency_code)], limit=1)
            if currency:
                invoice.currency_id = currency
            else:
                logs.append(_("Could not retrieve currency: %s. Did you enable the multicurrency option "
                              "and activate the currency?", invoice_currency_code))

        # ==== invoice date ====
        if issue_date := find_xml_value('.//IssueDate', tree):
            invoice.invoice_date = issue_date

        # ==== invoice_date_due ====
        if end_date := find_xml_value('.//InstallmentDueDate', tree):
            invoice.invoice_date_due = end_date

        # ==== ref ====
        if invoice_number := find_xml_value('.//InvoiceNumber', tree):
            invoice.ref = invoice_number

        # ==== narration ====
        invoice.narration = "\n".join(
            ref.text
            for ref in tree.xpath('.//LegalReference')
            if ref.text
        )

        # === invoice_line_ids ===
        logs += self._import_invoice_fill_lines(invoice, tree, ref_multiplier)

        body = Markup("<strong>%s</strong>") % _("Invoice imported from Factura-E XML file.")

        if logs:
            body += Markup("<ul>%s</ul>") \
                    % Markup().join(Markup("<li>%s</li>") % log for log in logs)

        invoice.message_post(body=body)

        return logs
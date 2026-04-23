def _check_move_configuration(self, invoice):
        """
            Override to add ZATCA compliance checks on the Invoice
        """

        journal = invoice.journal_id
        company = invoice.company_id

        errors = super()._check_move_configuration(invoice)
        if self.code != 'sa_zatca' or company.country_id and company.country_id.code != 'SA':
            return errors

        if invoice.commercial_partner_id == invoice.company_id.partner_id.commercial_partner_id:
            errors.append(_("- Invoice cannot be posted as the Supplier and Buyer are the same."))

        if not all(line.tax_ids for line in invoice.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and line._check_edi_line_tax_required())):
            errors.append(_("- Invoice lines need at least one tax. Please input it and try again."))

        if not journal._l10n_sa_ready_to_submit_einvoices():
            errors.append(_("- The Journal (%s) is not onboarded yet. Please onboard it and try again.", journal.name))

        if not company._l10n_sa_check_organization_unit():
            errors.append(
                _("- The company VAT identification must contain 15 digits, with the first and last digits being '3' as per the BR-KSA-39 and BR-KSA-40 of ZATCA KSA business rule."))
        if not journal.company_id.sudo().l10n_sa_private_key_id:
            errors.append(
                _("- No Private Key was generated for company %s. A Private Key is mandatory in order to generate Certificate Signing Requests (CSR).", company.name))

        supplier_missing_info = self._l10n_sa_check_seller_missing_info(invoice)
        customer_missing_info = self._l10n_sa_check_buyer_missing_info(invoice)

        if supplier_missing_info:
            errors.append(
                _(
                    "- Please set the following fields on the %(company_name)s: %(missing_fields)s",
                    company_name=company.name,
                    missing_fields=", ".join(supplier_missing_info),
                )
            )
        if customer_missing_info:
            errors.append(
                _(
                    "- %(missing_info)s",
                    missing_info=", ".join(customer_missing_info),
                )
            )
        if invoice.invoice_date > fields.Date.context_today(self.with_context(tz='Asia/Riyadh')):
            errors.append(_("- Please set the Invoice Date to be either less than or equal to today as per the Asia/Riyadh time zone, since ZATCA does not allow future-dated invoicing."))

        if invoice.l10n_sa_show_reason and not invoice.l10n_sa_reason:
            errors.append(_("- Please make sure the 'ZATCA Reason' for the issuance of the Credit/Debit Note is specified."))
        if invoice.l10n_sa_show_reason and not invoice._l10n_sa_check_billing_reference():
            errors.append(_("- Please make sure the 'Customer Reference' contains the sequential number of the original invoice(s) that the Credit/Debit Note is related to."))
        return errors
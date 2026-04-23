def _ubl_default_tax_category_grouping_key(self, base_line, tax_data, vals, currency):
        # EXTENDS account.edi.xml.ubl_bis3
        grouping_key = super()._ubl_default_tax_category_grouping_key(base_line, tax_data, vals, currency)
        if not grouping_key or not tax_data:
            return

        tax = tax_data['tax']
        hr_category = tax.l10n_hr_tax_category_id if tax else None

        # HR-BR-11: Each document-level expense (BG-21) that is not subject to VAT or is exempt from VAT must have
        # a document-level expense VAT category code (HR-BT-6) from table HR-TB-2 HR VAT category codes
        #   Instead of determining what the elements should be from the invoice details, here we directly use
        #   the data of the VAT expence category defined on the tax by the user
        if (
            tax.l10n_hr_tax_category_id
            and tax.amount_type == 'percent'
            and not tax.amount
        ):
            grouping_key.update({
                'tax_category_code': tax.l10n_hr_tax_category_id.code_untdid
            })
            # If account_edi_ubl_cii_tax_extension is installed and a value is specified, use that data, if not, override with HR data
            tax_extension = 'ubl_cii_tax_exemption_reason_code' in tax._fields and tax.ubl_cii_tax_exemption_reason_code
            if not tax_extension:
                grouping_key.update({'tax_exemption_reason': hr_category.description})

        if tax.tax_exigibility == 'on_payment':
            invoice_legal_notes_str = html2plaintext(tax.invoice_legal_notes or '') or "Obračun po naplaćenoj naknadi"
        else:
            invoice_legal_notes_str = None

        grouping_key.update({
            'hr_category_name': tax.l10n_hr_tax_category_id.name,
            'invoice_legal_notes_str': invoice_legal_notes_str,
        })
        return grouping_key
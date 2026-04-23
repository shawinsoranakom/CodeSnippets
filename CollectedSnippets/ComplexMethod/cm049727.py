def _l10n_tw_edi_check_before_generate_invoice_json(self):
        self.ensure_one()
        errors = []
        if not self.company_id.sudo().l10n_tw_edi_ecpay_merchant_id:
            errors.append(self.env._("Please fill in the ECpay API information in the Setting!"))

        if (self.l10n_tw_edi_is_print or self.partner_id.vat) and not self.partner_id.contact_address:
            errors.append(self.env._("Please fill in the customer address for printing Ecpay invoice."))

        if not self.partner_id.email and not self.partner_id.phone:
            errors.append(self.env._("Please fill in the customer email or phone number for Ecpay invoice creation."))

        if self.partner_id.phone:
            formatted_phone = self._reformat_phone_number(self.partner_id.phone)
            if not re.fullmatch(r'[\d]+', formatted_phone):
                errors.append(self.env._("Phone number contains invalid characters! It should be in the format: '+886 0997624293'."))

        if self.l10n_tw_edi_is_b2b and not self.partner_id.vat:
            errors.append(self.env._("A tax ID is required for company contact or individual contact under a company."))

        if self.l10n_tw_edi_is_b2b and self.partner_id.vat and (not self.partner_id.vat.isdigit() or len(self.partner_id.vat) != 8):
            errors.append(self.env._("The tax ID is invalid. It should be in the format: '12345678'."))

        errors.extend(self._l10n_tw_edi_check_tax_type_on_invoice_lines())

        tax_type, _, is_zero_tax_rate = self._l10n_tw_edi_determine_tax_types()

        if self.l10n_tw_edi_invoice_type == "07" and tax_type not in ["1", "2", "3", "9"]:
            errors.append(self.env._(
                "Invoice type 07 must be used with tax type 1, 2, 3 or 9. Please check the tax type on the invoice lines."
            ))

        if self.l10n_tw_edi_invoice_type == "08" and tax_type not in ["3", "4"]:
            errors.append(self.env._(
                "Invoice type 08 must be used with tax type 3 or 4. Please check the tax type on the invoice lines."
            ))

        if is_zero_tax_rate:
            if not self.l10n_tw_edi_clearance_mark or not self.l10n_tw_edi_zero_tax_rate_reason:
                errors.append(self.env._(
                    "Clearance mark and zero tax rate reason are required for a zero tax rate invoice."
                ))
        if errors:
            if 'website_id' in self._fields and self.website_id:
                self.message_post(body="Error:\n" + "\n".join(errors))
            else:
                raise UserError("Error:\n" + "\n".join(errors))
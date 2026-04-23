def _l10n_vn_edi_add_buyer_information(self, json_values):
        """ Create and return the buyer information for the current invoice. """
        self.ensure_one()

        commercial_partner_phone = self.commercial_partner_id.phone and self._l10n_vn_edi_format_phone_number(self.commercial_partner_id.phone)
        buyer_address = self.partner_id._display_address(without_company=True)
        formatted_address = ', '.join(part.strip() for part in buyer_address.splitlines() if part.strip())
        buyer_information = {
            'buyerName': self.partner_id.name,
            'buyerLegalName': self.commercial_partner_id.name,
            'buyerTaxCode': self.commercial_partner_id.vat or '',
            'buyerAddressLine': formatted_address,
            'buyerPhoneNumber': commercial_partner_phone or '',
            'buyerEmail': self.commercial_partner_id.email or '',
            'buyerCityName': self.partner_id.city or self.partner_id.state_id.name,
            'buyerCountryCode': self.partner_id.country_id.code,
            'buyerNotGetInvoice': 0,  # Set to 1 to no send the invoice to the buyer.
        }

        if self.partner_bank_id:
            buyer_information.update({
                'buyerBankName': self.partner_bank_id.bank_name,
                'buyerBankAccount': self.partner_bank_id.acc_number,
            })

        json_values['buyerInfo'] = buyer_information
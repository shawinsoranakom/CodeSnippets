def _l10n_ke_cu_open_invoice_message(self):
        """ Serialise the required fields for opening an invoice

        :returns: a list containing one byte-string representing the <CMD> and
                  <DATA> of the message sent to the fiscal device.
        """
        headquarter_address = (self.commercial_partner_id.street or '') + (self.commercial_partner_id.street2 or '')
        customer_address = (self.partner_id.street or '') + (self.partner_id.street2 or '')
        postcode_and_city = (self.partner_id.zip or '') + '' +  (self.partner_id.city or '')
        vat = (self.commercial_partner_id.vat or '').strip() if self.commercial_partner_id.country_id.code == 'KE' else ''
        invoice_elements = [
            b'1',                                                   # Reserved - 1 symbol with value '1'
            b'     0',                                              # Reserved - 6 symbols with value ‘     0’
            b'0',                                                   # Reserved - 1 symbol with value '0'
            b'1' if self.move_type == 'out_invoice' else b'A',      # 1 symbol with value '1' (new invoice), 'A' (credit note), or '@' (debit note)
            self._l10n_ke_fmt(self.commercial_partner_id.name, 30), # 30 symbols for Company name
            self._l10n_ke_fmt(vat, 14),                             # 14 Symbols for the client PIN number
            self._l10n_ke_fmt(headquarter_address, 30),             # 30 Symbols for customer headquarters
            self._l10n_ke_fmt(customer_address, 30),                # 30 Symbols for the address
            self._l10n_ke_fmt(postcode_and_city, 30),               # 30 symbols for the customer post code and city
            self._l10n_ke_fmt('', 30),                              # 30 symbols for the exemption number
        ]
        if self.move_type == 'out_refund':
            invoice_elements.append(self._l10n_ke_fmt(self.reversed_entry_id.l10n_ke_cu_invoice_number, 19)), # 19 symbols for related invoice number
        invoice_elements.append(re.sub('[^A-Za-z0-9 ]+', '', self.name)[-15:].ljust(15).encode('cp1251'))     # 15 symbols for trader system invoice number

        # Command: Open fiscal record (0x30)
        return [b'\x30' + b';'.join(invoice_elements)]
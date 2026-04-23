def _get_qr_code_vals_list(self, qr_method, amount, currency, debtor_partner, free_communication, structured_communication):
        tag, merchant_account_info = self._get_merchant_account_info()
        currency_code = CURRENCY_MAPPING[currency.name]
        if not currency.is_zero(amount):
            amount = amount.is_integer() and int(amount) or amount
        else:
            amount = None
        merchant_name = self.partner_id.name and self._remove_accents(self.partner_id.name)[:25] or 'NA'
        merchant_city = self.partner_id.city and self._remove_accents(self.partner_id.city)[:15] or ''
        comment = structured_communication or free_communication or ''
        comment = re.sub(r'[^ A-Za-z0-9_@.\\/#&+-]+', '', self._remove_accents(comment))
        additional_data_field = self._get_additional_data_field(comment) if self.include_reference else None
        merchant_category_code = self._get_merchant_category_code()
        return [
            (0, '01'),                                                              # Payload Format Indicator
            (1, '12'),                                                              # Dynamic QR Codes
            (tag, merchant_account_info),                                           # Merchant Account Information
            (52, merchant_category_code),                                           # Merchant Category Code
            (53, currency_code),                                                    # Transaction Currency
            (54, amount),                                                           # Transaction Amount
            (58, self.country_code),                                                # Country Code
            (59, merchant_name),                                                    # Merchant Name
            (60, merchant_city),                                                    # Merchant City
            (62, additional_data_field),                                            # Additional Data Field
        ]
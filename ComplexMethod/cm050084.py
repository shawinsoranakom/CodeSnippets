def _ubl_default_tax_category_grouping_key(self, base_line, tax_data, vals, currency):
        """ Give the values about the tax category for a given tax.

        :param base_line:   A base line (see '_prepare_base_line_for_taxes_computation').
        :param tax_data:    One of the tax data in base_line['tax_details']['taxes_data'].
        :param vals:        Some custom data.
        :param currency:    The currency for which the grouping key is expressed.
        :return:            A dictionary that could be used as a grouping key for the taxes helpers.
        """
        customer = vals['customer']
        supplier = vals['supplier']
        if tax_data and (
            tax_data['tax'].amount_type != 'percent'
            or self._ubl_is_recycling_contribution_tax(tax_data)
            or self._ubl_is_excise_tax(tax_data)
        ):
            return
        else:
            supplier_country_code = supplier.commercial_partner_id.country_id.code
            if supplier_country_code in GST_COUNTRY_CODES:
                scheme_id = 'GST'
            else:
                scheme_id = 'VAT'
            if self._ubl_is_reverse_charge_tax(tax_data):
                # Reverse-charge taxes with +100/-100% repartition lines are used in vendor bills.
                # In self-billed invoices, we report them from the seller's perspective, as 0% taxes.
                tax = tax_data['tax']
                return {
                    'tax_category_code': self._get_tax_category_code(customer.commercial_partner_id, supplier, tax),
                    **self._get_tax_exemption_reason(customer.commercial_partner_id, supplier, tax),
                    'percent': 0.0,
                    'scheme_id': scheme_id,
                    'is_withholding': False,
                    'currency': currency,
                }
            elif tax_data:
                tax = tax_data['tax']
                return {
                    'tax_category_code': self._get_tax_category_code(customer.commercial_partner_id, supplier, tax),
                    **self._get_tax_exemption_reason(customer.commercial_partner_id, supplier, tax),
                    'percent': tax.amount,
                    'scheme_id': scheme_id,
                    'is_withholding': tax.amount < 0.0,
                    'currency': currency,
                }
            else:
                return {
                    'tax_category_code': self._get_tax_category_code(customer.commercial_partner_id, supplier, self.env['account.tax']),
                    **self._get_tax_exemption_reason(customer.commercial_partner_id, supplier, self.env['account.tax']),
                    'percent': 0.0,
                    'scheme_id': scheme_id,
                    'is_withholding': False,
                    'currency': currency,
                }
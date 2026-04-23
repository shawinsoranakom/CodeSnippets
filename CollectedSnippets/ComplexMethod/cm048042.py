def _get_l10n_in_edi_line_details(self, index, line, line_tax_details):
        """
        Create the dictionary with line details
        """
        sign = self.is_inbound() and -1 or 1
        tax_details_by_code = self._get_l10n_in_tax_details_by_line_code(line_tax_details['tax_details'])
        quantity = line.quantity
        if line.discount == 100.00 or float_is_zero(quantity, 3):
            # Full discount or zero quantity
            unit_price_in_inr = line.currency_id._convert(
                line.price_unit,
                line.company_currency_id,
                line.company_id,
                line.date or fields.Date.context_today(self)
            )
        else:
            unit_price_in_inr = ((sign * line.balance) / (1 - (line.discount / 100))) / quantity

        if unit_price_in_inr < 0 and quantity < 0:
            # If unit price and quantity both is negative then
            # We set unit price and quantity as positive because
            # government does not accept negative in qty or unit price
            unit_price_in_inr = -unit_price_in_inr
            quantity = -quantity
        in_round = self._l10n_in_round_value
        line_details = {
            'SlNo': str(index),
            'IsServc': self._l10n_in_is_service_hsn(line.l10n_in_hsn_code) and 'Y' or 'N',
            'HsnCd': self._l10n_in_extract_digits(line.l10n_in_hsn_code),
            'Qty': in_round(quantity or 0.0, 3),
            'Unit': (
                line.product_uom_id.l10n_in_code
                and line.product_uom_id.l10n_in_code.split('-')[0]
                or 'OTH'
            ),
            # Unit price in company currency and tax excluded so its different then price_unit
            'UnitPrice': in_round(unit_price_in_inr, 3),
            # total amount is before discount
            'TotAmt': in_round(unit_price_in_inr * quantity),
            'Discount': in_round((unit_price_in_inr * quantity) * (line.discount / 100)),
            'AssAmt': in_round(sign * line.balance),
            'GstRt': in_round(
                (tax_details_by_code.get('igst_rate', 0.00)
                or (tax_details_by_code.get('cgst_rate', 0.00) + tax_details_by_code.get('sgst_rate', 0.00))),
                3
            ),
            'IgstAmt': in_round(tax_details_by_code.get('igst_amount', 0.00)),
            'CgstAmt': in_round(tax_details_by_code.get('cgst_amount', 0.00)),
            'SgstAmt': in_round(tax_details_by_code.get('sgst_amount', 0.00)),
            'CesRt': in_round(tax_details_by_code.get('cess_rate', 0.00), 3),
            'CesAmt': in_round(tax_details_by_code.get('cess_amount', 0.00)),
            'CesNonAdvlAmt': in_round(
                tax_details_by_code.get('cess_non_advol_amount', 0.00)
            ),
            'StateCesRt': in_round(tax_details_by_code.get('state_cess_rate_amount', 0.00), 3),
            'StateCesAmt': in_round(tax_details_by_code.get('state_cess_amount', 0.00)),
            'StateCesNonAdvlAmt': in_round(
                tax_details_by_code.get('state_cess_non_advol_amount', 0.00)
            ),
            'OthChrg': in_round(tax_details_by_code.get('other_amount', 0.00)),
            'TotItemVal': in_round((sign * line.balance) + line_tax_details.get('tax_amount', 0.00)),
        }
        if line.name:
            line_details['PrdDesc'] = line.name.replace("\n", "")[:300]
        return line_details
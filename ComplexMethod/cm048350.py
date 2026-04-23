def _prepare_ewaybill_tax_details_json_payload(self):
        round_value = self.env['account.move']._l10n_in_round_value
        tax_details = self.account_move_id._l10n_in_prepare_tax_details()
        tax_details_by_code = self.env['account.move']._get_l10n_in_tax_details_by_line_code(tax_details.get("tax_details", {}))
        invoice_line_tax_details = tax_details.get("tax_details_per_record")
        sign = self.account_move_id.is_inbound() and -1 or 1
        rounding_amount = sum(line.balance for line in self.account_move_id.line_ids if line.display_type == 'rounding') * sign
        total_invoice_value = tax_details.get("base_amount", 0.00) + tax_details.get("tax_amount", 0.00) + rounding_amount
        if self.account_move_id.l10n_in_gst_treatment == 'overseas' and self.partner_ship_to_id.country_id.code != 'IN':
            # For exports without LUT, the e-waybill total invoice value must include Reverse Charges.
            # Reverse charge amounts are stored as a negative value,
            # so we subtract it here to effectively add it to the total. (i.e. -(-x) = +x).
            adjusting_rc_amount = sum(
                tax_details_by_code.get(code, 0.00) for code in ("cgst_rc_amount", "sgst_rc_amount", "igst_rc_amount")
            )
            total_invoice_value -= adjusting_rc_amount
        return {
            "itemList": list(starmap(self._get_l10n_in_ewaybill_line_details, invoice_line_tax_details.items())),
            "totalValue": round_value(tax_details.get("base_amount", 0.00)),
            **{
                f'{tax_type}Value': round_value(tax_details_by_code.get(f'{tax_type}_amount', 0.00))
                for tax_type in ['cgst', 'sgst', 'igst', 'cess']
            },
            "cessNonAdvolValue": round_value(tax_details_by_code.get("cess_non_advol_amount", 0.00)),
            "otherValue": round_value(tax_details_by_code.get("other_amount", 0.00) + rounding_amount),
            "totInvValue": round_value(total_invoice_value),
        }
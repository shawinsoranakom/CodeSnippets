def _get_l10n_in_ewaybill_line_details(self, line, tax_details):
        sign = self.account_move_id.is_inbound() and -1 or 1
        extract_digits = self.env['account.move']._l10n_in_extract_digits
        round_value = self.env['account.move']._l10n_in_round_value
        tax_details_by_code = self.env['account.move']._get_l10n_in_tax_details_by_line_code(tax_details.get('tax_details', {}))
        line_details = {
            'productName': line.product_id.name[:100] if line.product_id else "",
            'hsnCode': extract_digits(line.l10n_in_hsn_code),
            'productDesc': line.name[:100] if line.name else "",
            'quantity': line.quantity,
            'qtyUnit': line.product_uom_id.l10n_in_code and line.product_uom_id.l10n_in_code.split('-')[0] or 'OTH',
            'taxableAmount': round_value(line.balance * sign),
        }
        gst_types = {'cgst', 'sgst', 'igst'}
        gst_tax_rates = {
            f"{gst_type}Rate": round_value(gst_tax_rate)
            for gst_type in gst_types
            if (gst_tax_rate := tax_details_by_code.get(f"{gst_type}_rate"))
        }
        line_details.update(
            gst_tax_rates or dict.fromkeys({f"{gst_type}Rate" for gst_type in gst_types}, 0.00)
        )
        if tax_details_by_code.get('cess_rate'):
            line_details.update({'cessRate': round_value(tax_details_by_code.get('cess_rate'))})
        return line_details
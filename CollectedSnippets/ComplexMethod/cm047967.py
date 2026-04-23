def _get_l10n_in_ewaybill_line_details(self, line, tax_details):
        if self.picking_id:
            AccountMove = self.env['account.move']
            product = line.product_id
            line_details = {
                'productName': product.name[:100],
                'hsnCode': AccountMove._l10n_in_extract_digits(product.l10n_in_hsn_code),
                'productDesc': line.description_picking[:100] if line.description_picking else "",
                'quantity': line.quantity,
                'qtyUnit': (
                    line.product_uom.l10n_in_code
                    and line.product_uom.l10n_in_code.split('-')[0]
                    or 'OTH'
                ),
                'taxableAmount': AccountMove._l10n_in_round_value(tax_details['total_excluded']),
            }
            gst_types = ('sgst', 'cgst', 'igst')
            gst_tax_rates = {}
            for tax in tax_details.get('taxes'):
                for gst_type in gst_types:
                    if tax_rate := tax.get(f'{gst_type}_rate'):
                        gst_tax_rates.update({
                            f"{gst_type}Rate": AccountMove._l10n_in_round_value(tax_rate)
                        })
                if cess_rate := tax.get("cess_rate"):
                    line_details['cessRate'] = AccountMove._l10n_in_round_value(cess_rate)
                if cess_non_advol := tax.get("cess_non_advol_amount"):
                    line_details['cessNonadvol'] = AccountMove._l10n_in_round_value(
                        cess_non_advol
                    )
            line_details.update(
                gst_tax_rates
                or dict.fromkeys(
                    [f"{gst_type}Rate" for gst_type in gst_types],
                    0
                )
            )
            return line_details
        return super()._get_l10n_in_ewaybill_line_details(line, tax_details)
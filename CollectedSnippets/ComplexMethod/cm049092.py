def _l10n_pl_edi_get_ksef_invoice_type(self):
        """
        Determines the specific TRodzajFaktury for KSeF.
        """
        self.ensure_one()

        # 1. Handle Corrections (Credit Notes)
        if self.move_type == 'out_refund':
            origin_inv = self.reversed_entry_id
            if not origin_inv:
                return 'KOR'

            origin_type = origin_inv._l10n_pl_edi_get_ksef_invoice_type()
            if origin_type == 'ZAL':
                return 'KOR_ZAL'
            elif origin_type == 'ROZ':
                return 'KOR_ROZ'
            else:
                return 'KOR'

        # 2. Handle Sales Invoices
        elif self.move_type == 'out_invoice':
            has_dp_lines = any(line._get_downpayment_lines() for line in self.invoice_line_ids)

            if has_dp_lines:
                # Check for Settlement (ROZ): Contains Regular lines AND Negative Downpayment lines
                has_regular_lines = any(not line._get_downpayment_lines() for line in self.invoice_line_ids)
                has_deducted_dp = any(line._get_downpayment_lines() and float_compare(line.price_subtotal, 0.0, precision_rounding=line.currency_id.rounding) == -1 for line in self.invoice_line_ids)

                if has_regular_lines and has_deducted_dp:
                    return 'ROZ'

                # If it's not ROZ but has downpayment lines (and they are positive), it is ZAL
                return 'ZAL'

        # Default to Standard VAT invoice
        return 'VAT'
def _compute_l10n_ch_qr_is_valid(self):
        for move in self:
            error_messages = move.partner_bank_id._get_error_messages_for_qr('ch_qr', move.partner_id, move.currency_id)
            move.l10n_ch_is_qr_valid = (
                move.move_type == 'out_invoice' and
                not error_messages and
                (
                    # QR codes must be printed on all Swiss transactions
                    move.company_id.account_fiscal_country_id.code == 'CH' or
                    (
                        # QR code is also printed if the fiscal country is not Switzerland but the receivale account is eligible
                        move.partner_bank_id.acc_type == 'iban' and
                        (iban := (move.partner_bank_id.acc_number or '').replace(' ', '')).startswith('CH') and
                        iban[4:9].isdigit() and
                        30000 <= int(iban[4:9]) <= 31999
                    )
                )
            )
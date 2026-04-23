def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()

        if self.company_id.country_id.code != 'VN' or not self.config_id.l10n_vn_auto_send_to_sinvoice:
            return vals

        sinvoice_symbol = self.config_id.l10n_vn_pos_symbol or self.config_id.company_id.l10n_vn_pos_default_symbol
        if sinvoice_symbol:
            vals['l10n_vn_edi_invoice_symbol'] = sinvoice_symbol.id

            # Refund Invoice (Credit Note)
            if self.amount_total < 0:
                vals['l10n_vn_edi_adjustment_type'] = '1'  # Money Adjustment

                reason = self.l10n_vn_credit_note_reason
                current_ref = vals.get('ref')
                if current_ref and reason:
                    vals['ref'] = f"{current_ref}, {reason}"

        return vals
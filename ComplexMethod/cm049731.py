def _is_tw_edi_issue_allowance_applicable(self, move):
        return (move.move_type == 'out_refund'
                and move.state == 'posted'
                and move.company_id.account_fiscal_country_id.code == 'TW'
                and move.reversed_entry_id
                and move.reversed_entry_id.l10n_tw_edi_ecpay_invoice_id
                and not move.l10n_tw_edi_refund_invoice_number
                and not move.l10n_tw_edi_refund_state
                and move.company_id._is_ecpay_enabled())
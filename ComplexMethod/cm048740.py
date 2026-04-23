def _sanitize_vals(self, vals):
        if 'debit' in vals or 'credit' in vals:
            vals = vals.copy()

            # This is used for negative amounts in debit/credit for manual inputs (to stay in same debit/credit as input)
            if vals.get('move_id') and self.env['account.move'].browse(vals['move_id']).company_id.account_storno:
                vals['is_storno'] = vals.get('is_storno', False) or (vals.get('debit', 0) < 0 or vals.get('credit', 0) < 0)

            debit = vals.pop('debit', 0)
            credit = vals.pop('credit', 0)
            if 'balance' not in vals:
                vals['balance'] = debit - credit
        if (
            vals.get('matching_number')
            and not vals['matching_number'].startswith('I')
            and not self.env.context.get('skip_matching_number_check')
        ):
            vals['matching_number'] = f"I{vals['matching_number']}"

        return vals
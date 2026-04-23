def write(self, vals):
        if self._is_write_forbidden(set(vals.keys())):
            raise UserError(_('Please close and validate the following open PoS Sessions before modifying this payment method.\n'
                            'Open sessions: %s', (' '.join(self.open_session_ids.mapped('name')),)))

        if 'payment_method_type' in vals:
            self._force_payment_method_type_values(vals, vals['payment_method_type'])
            return super().write(vals)

        pmt_terminal = self.filtered(lambda pm: pm.payment_method_type == 'terminal')
        pmt_qr = self.filtered(lambda pm: pm.payment_method_type == 'qr_code')
        not_pmt = self - pmt_terminal - pmt_qr

        res = True
        forced_vals = vals.copy()
        if pmt_terminal:
            self._force_payment_method_type_values(forced_vals, 'terminal', True)
            res = super(PosPaymentMethod, pmt_terminal).write(forced_vals) and res
        if pmt_qr:
            self._force_payment_method_type_values(forced_vals, 'qr_code', True)
            res = super(PosPaymentMethod, pmt_qr).write(forced_vals) and res
        if not_pmt:
            res = super(PosPaymentMethod, not_pmt).write(vals) and res

        return res
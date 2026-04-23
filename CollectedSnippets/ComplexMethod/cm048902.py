def action_post(self):
        # unlink checks if payment method code is not for checks. We do it on post and not when changing payment
        # method so that the user don't loose checks data in case of changing payment method and coming back again
        # also, changing partner recompute payment method so all checks would be cleaned
        for payment in self.filtered(lambda x: x.l10n_latam_new_check_ids and not x._is_latam_check_payment(check_subtype='new_check')):
            payment.l10n_latam_new_check_ids.unlink()
        if not self.env.context.get('l10n_ar_skip_remove_check'):
            for payment in self.filtered(lambda x: x.l10n_latam_move_check_ids and not x._is_latam_check_payment(check_subtype='move_check')):
                payment.l10n_latam_move_check_ids = False
        msgs = self._get_blocking_l10n_latam_warning_msg()
        if msgs:
            error_msg = "\n".join(f"* {msg}" for msg in msgs)
            raise ValidationError(error_msg)
        super().action_post()
        self._l10n_latam_check_split_move()
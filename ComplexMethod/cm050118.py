def _compute_amount(self):
        super()._compute_amount()
        for wizard in self:
            checks = wizard.l10n_latam_new_check_ids if wizard.filtered(lambda x: x._is_latam_check_payment(check_subtype='new_check')) else wizard.l10n_latam_move_check_ids
            checks_amount = sum(checks.mapped('amount'))
            if not wizard.currency_id.is_zero(checks_amount) and wizard.currency_id.compare_amounts(checks_amount, wizard.l10n_ar_net_amount) != 0:
                if wizard.partner_type == 'supplier':
                    original_amount = wizard.amount
                    f_delta = checks_amount - wizard.l10n_ar_net_amount
                    if f_delta < 0:
                        # Removing withholdings can result in an overshoot of the initial amount
                        wizard.amount = checks_amount
                        f_delta = checks_amount - wizard.l10n_ar_net_amount
                    d = f_delta
                    f_previous = wizard.l10n_ar_net_amount
                    wizard.amount += d
                    wizard._compute_l10n_ar_net_amount()
                    for i in range(201):
                        f_delta = checks_amount - wizard.l10n_ar_net_amount
                        if wizard.currency_id.is_zero(f_delta):
                            break
                        der = ((wizard.l10n_ar_net_amount - f_previous) / d) if abs(d) >= 0.01 else 1.0
                        if wizard.currency_id.is_zero(der):
                            i = 200
                            break
                        d = max(f_delta / der, 0.01)
                        f_previous = wizard.l10n_ar_net_amount
                        wizard.amount += d
                        wizard._compute_l10n_ar_net_amount()
                    if i == 200:
                        # Adjustment failed, resetting
                        wizard.amount = original_amount
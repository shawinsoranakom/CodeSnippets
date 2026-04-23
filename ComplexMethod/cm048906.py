def default_get(self, fields):
        res = super().default_get(fields)
        if 'check_ids' in fields and 'check_ids' not in res:
            if self.env.context.get('active_model') != 'l10n_latam.check':
                raise UserError(_("The register payment wizard should only be called on account.payment records."))
            checks = self.env['l10n_latam.check'].browse(self.env.context.get('active_ids', []))
            if checks.filtered(lambda x: x.payment_method_line_id.code != 'new_third_party_checks'):
                raise UserError(_('You have selected payments which are not checks. Please call this action from the Third Party Checks menu'))
            elif not all(check.payment_id.state not in ('draft', 'canceled') for check in checks):
                raise UserError(_("All the selected checks must be posted"))
            currency_ids = checks.mapped('currency_id')
            if any(x != currency_ids[0] for x in currency_ids):
                raise UserError(_("All the selected checks must use the same currency"))
            res['check_ids'] = checks.ids
        return res
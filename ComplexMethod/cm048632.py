def write(self, vals):
        if 'reconcile' in vals:
            if vals['reconcile']:
                self.filtered(lambda r: not r.reconcile)._toggle_reconcile_to_true()
            else:
                self.filtered(lambda r: r.reconcile)._toggle_reconcile_to_false()

        if vals.get('currency_id'):
            for account in self:
                if self.env['account.move.line'].search_count([('account_id', '=', account.id), ('currency_id', 'not in', (False, vals['currency_id']))]):
                    raise UserError(_('You cannot set a currency on this account as it already has some journal entries having a different foreign currency.'))

        if vals.get('deprecated') and self.env["account.tax.repartition.line"].search_count([('account_id', 'in', self.ids)], limit=1):
            raise UserError(_("You cannot deprecate an account that is used in a tax distribution."))

        res = super(AccountAccount, self.with_context(defer_account_code_checks=True, prefetch_fields=not any(field in vals for field in ['code', 'account_type']))).write(vals)

        if not self.env.context.get('defer_account_code_checks') and {'company_ids', 'code', 'code_mapping_ids'} & vals.keys():
            if 'company_ids' in vals:
                # Because writing on the field without sudo won't update the sudo cache (and vice versa)
                # we need to invalidate so that the sudo cache is up-to-date
                self.invalidate_recordset(fnames=['company_ids'])
            self._ensure_code_is_unique()

        return res
def _compute_distribution_analytic_account_ids(self):
        all_ids = {int(_id) for rec in self for key in (rec.analytic_distribution or {}) for _id in key.split(',') if _id.isdigit()}
        existing_accounts_ids = set(self.env['account.analytic.account'].browse(all_ids).exists().ids)
        for rec in self:
            ids = list(unique(int(_id) for key in (rec.analytic_distribution or {}) for _id in key.split(',') if _id.isdigit() and int(_id) in existing_accounts_ids))
            rec.distribution_analytic_account_ids = self.env['account.analytic.account'].browse(ids)
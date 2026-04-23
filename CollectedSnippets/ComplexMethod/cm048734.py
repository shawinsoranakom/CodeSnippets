def _compute_analytic_distribution(self):
        cache = {}
        for line in self:
            if line.display_type == 'product' or not line.move_id.is_invoice(include_receipts=True):
                related_distribution = line._related_analytic_distribution()
                root_plans = self.env['account.analytic.account'].browse(
                    list({int(account_id) for ids in related_distribution for account_id in ids.split(',') if account_id.strip()})
                ).exists().root_plan_id

                arguments = frozendict(line._get_analytic_distribution_arguments(root_plans))
                if arguments not in cache:
                    cache[arguments] = self.env['account.analytic.distribution.model']._get_distribution(arguments)
                line.analytic_distribution = related_distribution | cache[arguments] or line.analytic_distribution
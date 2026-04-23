def _compute_analytic_distribution(self):
        ctx_project = self.env['project.project'].browse(self.env.context.get('project_id'))
        project_lines = self.filtered(lambda l: not l.display_type and (ctx_project or l.product_id.with_company(l.company_id).project_id or l.order_id.project_id))
        empty_project_lines = project_lines.filtered(lambda l: not l.analytic_distribution)
        super(SaleOrderLine, (self - project_lines) + empty_project_lines)._compute_analytic_distribution()

        for line in project_lines:
            project = ctx_project or line.product_id.with_company(line.company_id).project_id or line.order_id.project_id
            if line.analytic_distribution:
                applied_root_plans = self.env['account.analytic.account'].browse(
                    list({int(account_id) for ids in line.analytic_distribution for account_id in ids.split(",")})
                ).exists().root_plan_id
                if accounts_to_add := project._get_analytic_accounts().filtered(
                    lambda account: account.root_plan_id not in applied_root_plans
                ):
                    # project account is added to each analytic distribution line
                    line.analytic_distribution = {
                        f"{account_ids},{','.join(map(str, accounts_to_add.ids))}": percentage
                        for account_ids, percentage in line.analytic_distribution.items()
                    }
            else:
                line.analytic_distribution = project._get_analytic_distribution()
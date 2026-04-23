def write(self, vals):
        new_parent = self.env['account.analytic.plan'].browse(vals.get('parent_id'))
        plan2previous_parent = {plan: plan.parent_id for plan in self if plan.parent_id}
        if 'parent_id' in vals and new_parent:
            # Update accounts in analytic lines before _sync_plan_column() unlinks child plan's column
            for plan in self:
                self.env['account.analytic.account']._update_accounts_in_analytic_lines(
                    new_fname=new_parent._column_name(),
                    current_fname=plan._column_name(),
                    accounts=self.env['account.analytic.account'].search([('plan_id', 'child_of', plan.id)]),
                )

        res = super().write(vals)

        if 'parent_id' in vals and not new_parent:
            # Update accounts in analytic lines after _sync_plan_column() creates the new column
            for plan, previous_parent in plan2previous_parent.items():
                self.env['account.analytic.account']._update_accounts_in_analytic_lines(
                    new_fname=plan._column_name(),
                    current_fname=previous_parent._column_name(),
                    accounts=self.env['account.analytic.account'].search([('plan_id', 'child_of', plan.id)]),
                )
        return res
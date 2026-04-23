def _prepare_invoice_line(self, **optional_values):
        """
            If the sale order line isn't linked to a sale order which already have a default analytic account,
            this method allows to retrieve the analytic account which is linked to project or task directly linked
            to this sale order line, or the analytic account of the project which uses this sale order line, if it exists.
        """
        values = super()._prepare_invoice_line(**optional_values)
        if not values.get('analytic_distribution') and not self.analytic_distribution:
            if self.task_id.project_id.account_id:
                values['analytic_distribution'] = {self.task_id.project_id.account_id.id: 100}
            elif self.project_id.account_id:
                values['analytic_distribution'] = {self.project_id.account_id.id: 100}
            elif self.is_service and not self.is_expense:
                [accounts] = self.env['project.project']._read_group([
                    ('account_id', '!=', False),
                    '|',
                        ('sale_line_id', '=', self.id),
                        ('tasks.sale_line_id', '=', self.id),
                ], aggregates=['account_id:recordset'])[0]
                if len(accounts) == 1:
                    values['analytic_distribution'] = {accounts.id: 100}
        return values
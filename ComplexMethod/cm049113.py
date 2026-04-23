def _timesheet_preprocess_get_accounts(self, vals):
        so_line = self.env['sale.order.line'].browse(vals.get('so_line'))
        if not (so_line and (distribution := so_line.sudo().analytic_distribution)):
            return super()._timesheet_preprocess_get_accounts(vals)

        company = self.env['res.company'].browse(vals.get('company_id'))
        accounts = self.env['account.analytic.account'].browse([
            int(account_id) for account_id in next(iter(distribution)).split(',')
        ]).exists()

        if not accounts:
            return super()._timesheet_preprocess_get_accounts(vals)

        plan_column_names = {account.root_plan_id._column_name() for account in accounts}
        mandatory_plans = [plan for plan in self._get_mandatory_plans(company, business_domain='timesheet') if plan['column_name'] != 'account_id']
        missing_plan_names = [plan['name'] for plan in mandatory_plans if plan['column_name'] not in plan_column_names]
        if missing_plan_names:
            raise ValidationError(_(
                "'%(missing_plan_names)s' analytic plan(s) required on the analytic distribution of the sale order item '%(so_line_name)s' linked to the timesheet.",
                missing_plan_names=missing_plan_names,
                so_line_name=so_line.name,
            ))

        account_id_per_fname = dict.fromkeys(self._get_plan_fnames(), False)
        for account in accounts:
            account_id_per_fname[account.root_plan_id._column_name()] = account.id
        return account_id_per_fname
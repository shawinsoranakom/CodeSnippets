def _timesheet_preprocess_get_accounts(self, vals):
        project = self.env['project.project'].sudo().browse(vals.get('project_id'))
        if not project:
            return {}
        company = self.env['res.company'].browse(vals.get('company_id'))
        mandatory_plans = [plan for plan in self._get_mandatory_plans(company, business_domain='timesheet') if plan['column_name'] != 'account_id']
        missing_plan_names = [plan['name'] for plan in mandatory_plans if not project[plan['column_name']]]
        if missing_plan_names:
            raise ValidationError(_(
                "'%(missing_plan_names)s' analytic plan(s) required on the project '%(project_name)s' linked to the timesheet.",
                missing_plan_names=missing_plan_names,
                project_name=project.name,
            ))
        return {
            fname: project[fname].id
            for fname in self._get_plan_fnames()
        }
def write(self, vals):
        values = vals
        self._check_can_write(values)

        task = self.env['project.task'].sudo().browse(values.get('task_id'))
        project = self.env['project.project'].sudo().browse(values.get('project_id'))
        if task and not task.project_id:
            raise ValidationError(_('Timesheets cannot be created on a private task.'))
        if project or task:
            values['company_id'] = task.company_id.id or project.company_id.id
        values.update({
            fname: account_id
            for fname, account_id in self._timesheet_preprocess_get_accounts(values).items()
            if fname not in values
        })

        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            if not employee.active:
                raise UserError(_('You cannot set an archived employee on existing timesheets.'))
        if 'name' in values and not values.get('name'):
            values['name'] = '/'
        if 'company_id' in values and not values.get('company_id'):
            del values['company_id']
        result = super().write(values)
        # applied only for timesheet
        self.filtered(lambda t: t.project_id)._timesheet_postprocess(values)
        return result
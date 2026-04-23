def create(self, vals_list):
        user_timezone = self.env.tz
        # Before creating a timesheet, we need to put a valid employee_id in the vals
        default_user_id = self._default_user()
        user_ids = []
        employee_ids = []
        # If batch creating from the calendar view, prefetch all employees to avoid fetching them one by one in the loop
        if self.env.context.get('timesheet_calendar'):
            self.env['hr.employee'].browse([vals.get('employee_id') for vals in vals_list])
        # 1/ Collect the user_ids and employee_ids from each timesheet vals
        skipped_vals = 0
        valid_vals = 0
        for vals in vals_list[:]:
            if self.env.context.get('timesheet_calendar'):
                if not 'employee_id' in vals:
                    vals['employee_id'] = self.env.user.employee_id.id
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                date = fields.Date.from_string(vals.get('date', fields.Date.to_string(fields.Date.context_today(self))))
                if not any(employee.resource_id._get_valid_work_intervals(
                    datetime.combine(date, time.min, tzinfo=user_timezone),
                    datetime.combine(date, time.max, tzinfo=user_timezone),
                )[0][employee.resource_id.id]):
                    vals_list.remove(vals)
                    skipped_vals += 1
                    continue
            task = self.env['project.task'].sudo().browse(vals.get('task_id'))
            project = self.env['project.project'].sudo().browse(vals.get('project_id'))
            if not (task or project):
                # It is not a timesheet
                continue
            elif task:
                if not task.project_id:
                    raise ValidationError(_('Timesheets cannot be created on a private task.'))
                if not project:
                    vals['project_id'] = task.project_id.id

            company = task.company_id or project.company_id or self.env['res.company'].browse(vals.get('company_id'))
            vals['company_id'] = company.id
            vals.update({
                fname: account_id
                for fname, account_id in self._timesheet_preprocess_get_accounts(vals).items()
                if fname not in vals
            })

            if not vals.get('product_uom_id'):
                vals['product_uom_id'] = company.project_time_mode_id.id

            if not vals.get('name'):
                vals['name'] = '/'
            employee_id = vals.get('employee_id', self.env.context.get('default_employee_id', False))
            if employee_id and employee_id not in employee_ids:
                employee_ids.append(employee_id)
            else:
                user_id = vals.get('user_id', default_user_id)
                if user_id not in user_ids:
                    user_ids.append(user_id)
            valid_vals += 1

        # 2/ Search all employees related to user_ids and employee_ids, in the selected companies
        HrEmployee_sudo = self.env['hr.employee'].sudo()
        employees = HrEmployee_sudo.search([
            '&', '|', ('user_id', 'in', user_ids), ('id', 'in', employee_ids), ('company_id', 'in', self.env.companies.ids)
        ])

        #                 ┌───── in search results = active/in companies ────────> was found with... ─── employee_id ───> (A) There is nothing to do, we will use this employee_id
        # 3/ Each employee                                                                          └──── user_id ──────> (B)** We'll need to select the right employee for this user
        #                 └─ not in search results = archived/not in companies ──> (C) We raise an error as we can't create a timesheet for an archived employee
        # ** We can rely on the user to get the employee_id if
        #    he has an active employee in the company of the timesheet
        #    or he has only one active employee for all selected companies
        valid_employee_per_id = {}
        employee_id_per_company_per_user = defaultdict(dict)
        for employee in employees:
            if employee.id in employee_ids:
                valid_employee_per_id[employee.id] = employee
            else:
                employee_id_per_company_per_user[employee.user_id.id][employee.company_id.id] = employee.id

        # 4/ Put valid employee_id in each vals
        error_msg = _('Timesheets must be created with an active employee in the selected companies.')
        for vals in vals_list:
            if not vals.get('project_id'):
                continue
            employee_in_id = vals.get('employee_id', self.env.context.get('default_employee_id', False))
            if employee_in_id:
                company = False
                if not vals.get('company_id'):
                    company = HrEmployee_sudo.browse(employee_in_id).company_id
                    vals['company_id'] = company.id
                if not vals.get('product_uom_id'):
                    vals['product_uom_id'] = company.project_time_mode_id.id if company else self.env['res.company'].browse(vals.get('company_id', self.env.company.id)).project_time_mode_id.id
                if employee_in_id in valid_employee_per_id:
                    vals['user_id'] = valid_employee_per_id[employee_in_id].sudo().user_id.id   # (A) OK
                    continue
                else:
                    raise ValidationError(error_msg)                                            # (C) KO
            else:
                user_id = vals.get('user_id', default_user_id)                                  # (B)...

            # ...Look for an employee, with ** conditions
            employee_per_company = employee_id_per_company_per_user.get(user_id)
            employee_out_id = False
            if employee_per_company:
                company_id = list(employee_per_company)[0] if len(employee_per_company) == 1\
                        else vals.get('company_id') or self.env.company.id
                employee_out_id = employee_per_company.get(company_id, False)

            if employee_out_id:
                vals['employee_id'] = employee_out_id
                vals['user_id'] = user_id
                company = False
                if not vals.get('company_id'):
                    company = HrEmployee_sudo.browse(employee_out_id).company_id
                    vals['company_id'] = company.id
                if not vals.get('product_uom_id'):
                    vals['product_uom_id'] = company.project_time_mode_id.id if company else self.env['res.company'].browse(vals.get('company_id', self.env.company.id)).project_time_mode_id.id
            else:  # ...and raise an error if they fail
                raise ValidationError(error_msg)

        # 5/ Finally, create the timesheets
        lines = super().create(vals_list)
        lines._check_can_create()
        for line, values in zip(lines, vals_list):
            if line.project_id:  # applied only for timesheet
                line._timesheet_postprocess(values)

        if self.env.context.get('timesheet_calendar'):
            if skipped_vals:
                type = "danger"
                if valid_vals:
                    message = self.env._("Some timesheets were not created: employees aren’t working on the selected days")
                else:
                    message = self.env._("No timesheets created: employees aren’t working on the selected days")
            else:
                type = "success"
                message = self.env._("Timesheets successfully created")

            self.env.user._bus_send('simple_notification', {
                "type": type,
                "message": message,
            })

        return lines
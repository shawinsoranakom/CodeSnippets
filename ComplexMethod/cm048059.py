def _compute_resource_calendar_id(self):
        leaves_without_emp_or_date = self.filtered(
            lambda leave: not (leave.employee_id and leave.request_date_from and leave.request_date_to)
        )
        valid_leaves = self - leaves_without_emp_or_date
        leaves_without_emp_or_date.resource_calendar_id = self.env.company.resource_calendar_id
        if not valid_leaves:
            return
        employees_by_dates = defaultdict(lambda: self.env['hr.employee'])
        contracts_by_employee = dict(
            self.env['hr.version']._read_group(
                domain=[('employee_id', 'in', self.employee_id.ids)],
                groupby=['employee_id'],
                aggregates=['id:recordset']
            )
        )
        for leave in valid_leaves:
            employees_by_dates[leave.request_date_from] += leave.employee_id
        calendar_by_dates = {date_from: employees._get_calendars(date_from) for date_from, employees in employees_by_dates.items()}
        for leave in valid_leaves:
            calendar = calendar_by_dates.get(leave.request_date_from, {}).get(leave.employee_id.id) \
                        or self.env.company.resource_calendar_id
            # We use the request dates to find the contracts, because date_from
            # and date_to are not set yet at this point. Since these dates are
            # used to get the contracts for which these leaves apply and
            # contract start- and end-dates are just dates (and not datetimes)
            # these dates are comparable.
            contracts = contracts_by_employee.get(leave.employee_id, self.env['hr.version']).filtered(
                lambda c: c.date_start <= leave.request_date_to and
                          (not c.date_end or c.date_end >= leave.request_date_from))
            if contracts:
                # If there are more than one contract they should all have the
                # same calendar, otherwise a constraint is violated.
                calendar = contracts[:1].resource_calendar_id
            leave.resource_calendar_id = calendar
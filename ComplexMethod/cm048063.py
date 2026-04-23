def _get_durations(self, check_leave_type=True, resource_calendar=None):
        """
        This method is factored out into a separate method from
        _compute_duration so it can be hooked and called without necessarily
        modifying the fields and triggering more computes of fields that
        depend on number_of_hours or number_of_days.
        """
        result = {}
        employee_leaves = self.filtered('employee_id')
        employees_by_dates_calendar = defaultdict(lambda: self.env['hr.employee'])
        for leave in employee_leaves:
            if not leave.date_from or not leave.date_to:
                continue
            employees_by_dates_calendar[(leave.date_from, leave.date_to, leave.holiday_status_id.include_public_holidays_in_duration, resource_calendar or leave.resource_calendar_id)] += leave.employee_id
        # We force the company in the domain as we are more than likely in a compute_sudo
        domain = [('time_type', '=', 'leave'),
                  ('company_id', 'in', self.env.companies.ids + self.env.context.get('allowed_company_ids', [])),
                  # When searching for resource leave intervals, we exclude the one that
                  # is related to the leave we're currently trying to compute for.
                  '|', ('holiday_id', '=', False), ('holiday_id', 'not in', employee_leaves.ids)]
        # Precompute values in batch for performance purposes
        work_time_per_day_mapped = {
            (date_from, date_to, include_public_holidays_in_duration, calendar): employees.with_context(
                    compute_leaves=not include_public_holidays_in_duration)._list_work_time_per_day(date_from, date_to, domain=domain, calendar=calendar)
            for (date_from, date_to, include_public_holidays_in_duration, calendar), employees in employees_by_dates_calendar.items()
        }
        work_days_data_mapped = {
            (date_from, date_to, include_public_holidays_in_duration, calendar): employees._get_work_days_data_batch(date_from, date_to, compute_leaves=not include_public_holidays_in_duration, domain=domain, calendar=calendar)
            for (date_from, date_to, include_public_holidays_in_duration, calendar), employees in employees_by_dates_calendar.items()
        }
        for leave in self:
            calendar = resource_calendar or leave.resource_calendar_id
            if not leave.date_from or not leave.date_to or (not calendar and not leave.employee_id):
                result[leave.id] = (0, 0)
                continue
            hours, days = (0, 0)
            if leave.employee_id:
                # For flexible employees, if it's a single day leave, we force it to the real duration since the virtual intervals might not match reality on that day, especially for custom hours
                # sudo as is_flexible is on version model and employee does not have access to it.
                if leave.employee_id.sudo().is_flexible and leave.request_date_to == leave.request_date_from:
                    public_holidays = self.env['resource.calendar.leaves'].search([
                        ('resource_id', '=', False),
                        ('date_from', '<', leave.date_to),
                        ('date_to', '>', leave.date_from),
                        ('calendar_id', 'in', [False, calendar.id]),
                        ('company_id', '=', leave.company_id.id)
                    ])
                    if public_holidays:
                        public_holidays_intervals = Intervals([(ph.date_from, ph.date_to, ph) for ph in public_holidays])
                        leave_intervals = Intervals([(leave.date_from, leave.date_to, leave)])
                        real_leave_intervals = leave_intervals - public_holidays_intervals
                        hours = 0
                        for start, stop, meta in real_leave_intervals:
                            hours += (stop - start).total_seconds() / 3600
                    else:
                        hours = (leave.date_to - leave.date_from).total_seconds() / 3600
                    if not leave.request_unit_hours and not public_holidays:
                        days = 1 if not leave.request_unit_half or leave.request_date_from_period != leave.request_date_to_period else 0.5
                    else:
                        days = hours / 24
                elif leave.leave_type_request_unit == 'day' and check_leave_type:
                    # list of tuples (day, hours)
                    work_time_per_day_list = work_time_per_day_mapped[leave.date_from, leave.date_to, leave.holiday_status_id.include_public_holidays_in_duration, calendar][leave.employee_id.id]
                    days = len(work_time_per_day_list)
                    hours = sum(map(lambda t: t[1], work_time_per_day_list))
                else:
                    work_days_data = work_days_data_mapped[leave.date_from, leave.date_to, leave.holiday_status_id.include_public_holidays_in_duration, calendar][leave.employee_id.id]
                    hours, days = work_days_data['hours'], work_days_data['days']
            else:
                today_hours = calendar.get_work_hours_count(
                    datetime.combine(leave.date_from.date(), time.min),
                    datetime.combine(leave.date_from.date(), time.max),
                    False)
                hours = calendar.get_work_hours_count(leave.date_from, leave.date_to, compute_leaves=not leave.holiday_status_id.include_public_holidays_in_duration)
                days = hours / (today_hours or HOURS_PER_DAY)
            if leave.leave_type_request_unit == 'day' and check_leave_type:
                days = ceil(days)
            result[leave.id] = (days, hours)
        return result
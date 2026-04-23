def _get_schedule(self, start_period, stop_period, everybody=False, merge=True):
        """
        This method implements the general case where employees might have different resource calendars at different
        times, even though this is not the case with only this module installed.
        This way it will work with these other modules by just overriding
        `_get_calendar_periods`.

        :param datetime start_period: the start of the period
        :param datetime stop_period: the stop of the period
        :param boolean everybody: represents the "everybody" filter on calendar
        :param boolean merge: specifies if calendar's work_intervals needs to be merged
        :return: schedule (merged or not) by partner
        :rtype: defaultdict
        """
        employees_by_partner = self._get_employees_from_attendees(everybody)
        if not employees_by_partner:
            return {}
        interval_by_calendar = defaultdict()
        calendar_periods_by_employee = defaultdict(list)
        resources_by_calendar = defaultdict(lambda: self.env['resource.resource'])

        # Compute employee's calendars's period and order employee by his involved calendars
        employees = sum(employees_by_partner.values(), start=self.env['hr.employee'])
        calendar_periods_by_employee = employees._get_calendar_periods(start_period, stop_period)
        for employee, calendar_periods in calendar_periods_by_employee.items():
            for _start, _stop, calendar in calendar_periods:
                calendar = calendar or self.env.company.resource_calendar_id
                resources_by_calendar[calendar] += employee.resource_id

        # Compute all work intervals per calendar
        for calendar, resources in resources_by_calendar.items():
            work_intervals = calendar._work_intervals_batch(start_period, stop_period, resources=resources, tz=timezone(calendar.tz))
            del work_intervals[False]
            # Merge all employees intervals to avoid to compute it multiples times
            if merge:
                interval_by_calendar[calendar] = reduce(Intervals.__and__, work_intervals.values())
            else:
                interval_by_calendar[calendar] = work_intervals

        # Compute employee's schedule based own his calendar's periods
        schedule_by_employee = defaultdict(list)
        for employee, calendar_periods in calendar_periods_by_employee.items():
            employee_interval = Intervals([])
            for (start, stop, calendar) in calendar_periods:
                calendar = calendar or self.env.company.resource_calendar_id # No calendar if fully flexible
                interval = Intervals([(start, stop, self.env['resource.calendar'])])
                if merge:
                    calendar_interval = interval_by_calendar[calendar]
                else:
                    calendar_interval = interval_by_calendar[calendar][employee.resource_id.id]
                employee_interval = employee_interval | (calendar_interval & interval)
            schedule_by_employee[employee] = employee_interval

        # Compute partner's schedule equals to the union between his employees's schedule
        schedules = defaultdict()
        for partner, employees in employees_by_partner.items():
            partner_schedule = Intervals([])
            for employee in employees:
                if schedule_by_employee[employee]:
                    partner_schedule = partner_schedule | schedule_by_employee[employee]
            schedules[partner] = partner_schedule
        return schedules
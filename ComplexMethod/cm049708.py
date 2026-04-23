def _get_durations(self, check_leave_type=True, resource_calendar=None):
        """
        In french time off laws, if an employee has a part time contract, when taking time off
        before one of his off day (compared to the company's calendar) it should also count the time
        between the time off and the next calendar work day/company off day (weekends).

        For example take an employee working mon-wed in a company where the regular calendar is mon-fri.
        If the employee were to take a time off ending on wednesday, the legal duration would count until friday.
        """
        if not resource_calendar:
            fr_leaves = self.filtered(lambda leave: leave._l10n_fr_leave_applies())
            duration_by_leave_id = super(HrLeave, self - fr_leaves)._get_durations(resource_calendar=resource_calendar)
            fr_leaves_by_company = fr_leaves.grouped('company_id')
            if fr_leaves:
                public_holidays = self.env['resource.calendar.leaves'].search([
                    ('resource_id', '=', False),
                    ('company_id', 'in', fr_leaves.company_id.ids + [False]),
                    ('date_from', '<', max(fr_leaves.mapped('date_to')) + relativedelta(days=1)),
                    ('date_to', '>', min(fr_leaves.mapped('date_from')) - relativedelta(days=1)),
                ])
            for company, leaves in fr_leaves_by_company.items():
                company_cal = company.resource_calendar_id
                holidays_days_list = []
                public_holidays_filtered = public_holidays.filtered_domain([
                    ('calendar_id', 'in', [False, company_cal.id]),
                    ('company_id', '=', company.id)
                ])
                for holiday in public_holidays_filtered:
                    tz = pytz.timezone(holiday.write_uid.tz)
                    current = holiday.date_from.replace(tzinfo=pytz.utc).astimezone(tz).date()
                    holiday_date_to = holiday.date_to.replace(tzinfo=pytz.utc).astimezone(tz).date()
                    while current <= holiday_date_to:
                        holidays_days_list.append(current)
                        current += relativedelta(days=1)
                for leave in leaves:
                    if leave.request_unit_half:
                        duration_by_leave_id.update(leave._get_durations(resource_calendar=company_cal))
                        continue
                    # Extend the end date to next working day
                    date_start = leave.date_from
                    date_end = leave.date_to
                    while not leave.resource_calendar_id._works_on_date(date_start):
                        date_start += relativedelta(days=1)
                    extended_date_end = date_end
                    while not company_cal._works_on_date(extended_date_end + relativedelta(days=1)):
                        extended_date_end += relativedelta(days=1)
                    # Count number of days in company calendar
                    current = date_start.date()
                    end_date = extended_date_end.date()
                    legal_days = 0.0
                    while current <= end_date:
                        if current in holidays_days_list:
                            current += relativedelta(days=1)
                            continue
                        if company_cal._works_on_date(current):
                            legal_days += 1.0
                        current += relativedelta(days=1)
                    standard_duration = super()._get_durations(resource_calendar=resource_calendar)
                    _, hours = standard_duration.get(leave.id, (0.0, 0.0))

                    duration_by_leave_id[leave.id] = (legal_days, hours)

            return duration_by_leave_id
        return super()._get_durations(resource_calendar=resource_calendar)
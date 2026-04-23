def _get_fr_date_from_to(self, date_from, date_to):
        self.ensure_one()
        # What we need to compute is how much we will need to push date_to in order to account for the lost days
        # This gets even more complicated in two_weeks_calendars

        # The following computation doesn't work for resource calendars in
        # which the employee works zero hours.
        if not (self.resource_calendar_id.attendance_ids):
            raise UserError(_("An employee can't take paid time off in a period without any work hours."))

        if not self.request_unit_hours:
            # Use company's working schedule hours for the leave to avoid duration calculation issues.
            def adjust_date_range(date_from, date_to, from_period, to_period, attendance_ids, employee_id):
                period_ids_from = attendance_ids.filtered(lambda a: a.day_period in from_period
                                                                    and int(a.dayofweek) == date_from.weekday()
                                                                    and (not a.two_weeks_calendar or int(a.week_type) == a.get_week_type(date_from))
                                                                    and not a.display_type)
                period_ids_to = attendance_ids.filtered(lambda a: a.day_period in to_period
                                                                    and int(a.dayofweek) == date_to.weekday()
                                                                    and (not a.two_weeks_calendar or int(a.week_type) == a.get_week_type(date_to))
                                                                    and not a.display_type)
                if period_ids_from:
                    min_hour = min(attendance.hour_from for attendance in period_ids_from)
                    date_from = self._to_utc(date_from, min_hour, employee_id)
                if period_ids_to:
                    max_hour = max(attendance.hour_to for attendance in period_ids_to)
                    date_to = self._to_utc(date_to, max_hour, employee_id)
                return date_from, date_to

            if self.request_unit_half:
                from_period = ['morning'] if self.request_date_from_period == 'am' else ['afternoon']
                to_period = ['morning'] if self.request_date_to_period == 'am' else ['afternoon']
            else:
                from_period = ['morning', 'afternoon']
                to_period = ['morning', 'afternoon']
            attendance_ids = self.company_id.resource_calendar_id.attendance_ids | self.resource_calendar_id.attendance_ids
            date_from, date_to = adjust_date_range(date_from, date_to, from_period, to_period, attendance_ids, self.employee_id)

        similar = date_from.date() == date_to.date() and self.request_date_from_period == self.request_date_to_period
        if self.request_unit_half and similar and self.request_date_from_period == 'am':
            # In normal workflows request_unit_half implies that date_from and date_to are the same
            # request_unit_half allows us to choose between `am` and `pm`
            # In a case where we work from mon-wed and request a half day in the morning
            # we do not want to push date_to since the next work attendance is actually in the afternoon
            date_from_weektype = str(self.env['resource.calendar.attendance'].get_week_type(date_from))
            date_from_dayofweek = str(date_from.weekday())
            # Fetch the attendances we care about
            attendance_ids = self.resource_calendar_id.attendance_ids.filtered(lambda a:
                a.dayofweek == date_from_dayofweek
                and a.day_period != "lunch"
                and (not self.resource_calendar_id.two_weeks_calendar or a.week_type == date_from_weektype))
            if len(attendance_ids) == 2:
                # The employee took the morning off on a day where he works the afternoon aswell
                return (date_from, date_to)

        # Check calendars for working days until we find the right target, start at date_to + 1 day
        # Postpone date_target until the next working day
        date_start = date_from
        date_target = date_to
        # It is necessary to move the start date up to the first work day of
        # the employee calendar as otherwise days worked on by the company
        # calendar before the actual start of the leave would be taken into
        # account.
        while not self.resource_calendar_id._works_on_date(date_start):
            date_start += relativedelta(days=1)
        while not self.resource_calendar_id._works_on_date(date_target + relativedelta(days=1)):
            date_target += relativedelta(days=1)

        # Undo the last day increment
        return (date_start, date_target)
def _format_leave(self, leave, resource_hours_per_day, resource_hours_per_week, ranges_to_remove, start_day, end_day, locale):
        leave_start = leave[0]
        leave_record = leave[2]
        holiday_id = leave_record.holiday_id
        tz = pytz.timezone(self.tz or self.env.user.tz)

        if holiday_id.request_unit_half:
            # Half day leaves are limited to half a day within a single day
            leave_day = leave_start.date()
            half_start_datetime = tz.localize(datetime.combine(leave_day, datetime.min.time() if holiday_id.request_date_from_period == "am" else time(12)))
            half_end_datetime = tz.localize(datetime.combine(leave_day, time(12) if holiday_id.request_date_from_period == "am" else datetime.max.time()))
            ranges_to_remove.append((half_start_datetime, half_end_datetime, self.env['resource.calendar.attendance']))

            if not self._is_fully_flexible():
                # only days inside the original period
                if leave_day >= start_day and leave_day <= end_day:
                    resource_hours_per_day[self.id][leave_day] -= holiday_id.number_of_hours
                week = weeknumber(babel_locale_parse(locale), leave_day)
                resource_hours_per_week[self.id][week] -= holiday_id.number_of_hours
        elif holiday_id.request_unit_hours:
            # Custom leaves are limited to a specific number of hours within a single day
            leave_day = leave_start.date()
            range_start_datetime = pytz.utc.localize(leave_record.date_from).replace(tzinfo=None).astimezone(tz)
            range_end_datetime = pytz.utc.localize(leave_record.date_to).replace(tzinfo=None).astimezone(tz)
            ranges_to_remove.append((range_start_datetime, range_end_datetime, self.env['resource.calendar.attendance']))

            if not self._is_fully_flexible():
                # only days inside the original period
                if leave_day >= start_day and leave_day <= end_day:
                    resource_hours_per_day[self.id][leave_day] -= holiday_id.number_of_hours
                week = weeknumber(babel_locale_parse(locale), leave_day)
                resource_hours_per_week[self.id][week] -= holiday_id.number_of_hours
        else:
            super()._format_leave(leave, resource_hours_per_day, resource_hours_per_week, ranges_to_remove, start_day, end_day, locale)
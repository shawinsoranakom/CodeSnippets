def _prepare_holidays_meeting_values(self):
        result = defaultdict(list)
        for holiday in self:
            user = holiday.user_id
            meeting_name = _(
                "%(employee)s on Time Off : %(duration)s",
                employee=holiday.employee_id.name or holiday.category_id.name,
                duration=holiday.duration_display)
            allday_value = not holiday.request_unit_half or holiday.request_date_from_period == 'am' and holiday.request_date_to_period == 'pm'
            if holiday.leave_type_request_unit == 'hour':
                allday_value = float_compare(holiday.number_of_days, 1.0, 1) >= 0

            if allday_value:
                # `start` and `stop` are not in UTC for allday events
                leave_tz = pytz.timezone(holiday.tz) if holiday.tz else pytz.UTC
                start_value = pytz.UTC.localize(holiday.date_from).astimezone(leave_tz).replace(tzinfo=None)
                stop_value = pytz.UTC.localize(holiday.date_to).astimezone(leave_tz).replace(tzinfo=None)
            else:
                start_value = holiday.date_from
                stop_value = holiday.date_to

            meeting_values = {
                'name': meeting_name,
                'duration': holiday.number_of_days * (holiday.resource_calendar_id.hours_per_day or HOURS_PER_DAY),
                'description': holiday.notes,
                'user_id': user.id,
                'start': start_value,
                'stop': stop_value,
                'allday': allday_value,
                'privacy': 'confidential',
                'event_tz': user.tz,
                'activity_ids': [(5, 0, 0)],
                'res_id': holiday.id,
            }
            # Add the partner_id (if exist) as an attendee
            partner_id = (user and user.partner_id) or (holiday.employee_id and holiday.employee_id.work_contact_id)
            if partner_id:
                meeting_values['partner_ids'] = [(4, partner_id.id)]
            result[user.id].append(meeting_values)
        return result
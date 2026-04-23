def _prepare_public_holidays_values(self, vals_list):
        for vals in vals_list:
            # Manage the case of create a Public Time Off in another timezone
            # The datetime created has to be in UTC for the calendar's timezone
            if not vals.get('calendar_id') or vals.get('resource_id') or \
                not isinstance(vals.get('date_from'), (datetime, str)) or \
                not isinstance(vals.get('date_to'), (datetime, str)):
                continue
            user_tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
            calendar_tz = pytz.timezone(self.env['resource.calendar'].browse(vals['calendar_id']).tz)
            if user_tz != calendar_tz:
                datetime_from = self._ensure_datetime(vals['date_from'], '%Y-%m-%d %H:%M:%S')
                datetime_to = self._ensure_datetime(vals['date_to'], '%Y-%m-%d %H:%M:%S')
                if datetime_from and datetime_to:
                    vals['date_from'] = self._convert_timezone(datetime_from, user_tz, calendar_tz)
                    vals['date_to'] = self._convert_timezone(datetime_to, user_tz, calendar_tz)
        return vals_list
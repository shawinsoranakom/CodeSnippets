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
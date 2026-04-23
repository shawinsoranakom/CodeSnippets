def _compute_hours_last_month(self):
        """
        Compute hours and overtime hours in the current month, if we are the 15th of october, will compute from 1 oct to 15 oct
        """
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for timezone, employees in self.grouped('tz').items():
            tz = pytz.timezone(timezone or 'UTC')
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            end_tz = now_tz
            end_naive = end_tz.astimezone(pytz.utc).replace(tzinfo=None)

            for employee in employees:
                current_month_attendances = employee.attendance_ids.filtered(
                    lambda att: att.check_in >= start_naive and att.check_out and att.check_out <= end_naive
                )
                hours = 0
                overtime_hours = 0
                for att in current_month_attendances:
                    hours += att.worked_hours or 0
                    overtime_hours += att.validated_overtime_hours or 0
                employee.hours_last_month = round(hours, 2)
                employee.hours_last_month_display = "%g" % employee.hours_last_month
                # overtime_adjustments = sum(
                #     ot.duration or 0
                #     for ot in employee.overtime_ids.filtered(
                #         lambda ot: ot.date >= start_tz.date() and ot.date <= end_tz.date() and ot.adjustment
                #     )
                # )
                employee.hours_last_month_overtime = round(overtime_hours, 2)
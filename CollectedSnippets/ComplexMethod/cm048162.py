def _compute_display_name(self):
        super()._compute_display_name()
        if self.env.context.get('hr_timesheet_display_remaining_hours'):
            for task in self:
                if task.allow_timesheets and task.allocated_hours > 0 and task.encode_uom_in_days:
                    days_left = _("(%s days remaining)", task._convert_hours_to_days(task.remaining_hours))
                    task.display_name = task.display_name + "\u00A0" + days_left
                elif task.allow_timesheets and task.allocated_hours > 0:
                    hours, mins = (str(int(duration)).rjust(2, '0') for duration in divmod(abs(task.remaining_hours) * 60, 60))
                    hours_left = _(
                        "(%(sign)s%(hours)s:%(minutes)s remaining)",
                        sign='-' if task.remaining_hours < 0 else '',
                        hours=hours,
                        minutes=mins,
                    )
                    task.display_name = task.display_name + "\u00A0" + hours_left
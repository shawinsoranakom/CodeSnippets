def _compute_display_name(self):
        for leave in self:
            user_tz = pytz.timezone(leave.tz)
            date_from_utc = leave.date_from and leave.date_from.astimezone(user_tz).date()
            date_to_utc = leave.date_to and leave.date_to.astimezone(user_tz).date()
            time_off_type_display = leave.holiday_status_id.name
            if self.env.context.get('short_name'):
                short_leave_name = leave.name or time_off_type_display or _('Time Off')
                leave.display_name = _("%(name)s: %(duration)s", name=short_leave_name, duration=leave.duration_display)
            else:
                target = leave.employee_id.name or ""
                display_date = format_date(self.env, date_from_utc) or ""
                if leave.number_of_days > 1 and date_from_utc and date_to_utc:
                    display_date += _(' to %(date_to_utc)s',
                        date_to_utc=format_date(self.env, date_to_utc) or ""
                    )
                if not target or self.env.context.get('hide_employee_name') and 'employee_id' in self.env.context.get('group_by', []):
                    leave.display_name = _("%(leave_type)s: %(duration)s (%(start)s)",
                        leave_type=time_off_type_display,
                        duration=leave.duration_display,
                        start=display_date,
                    )
                elif not time_off_type_display:
                    leave.display_name = _("%(person)s: %(duration)s (%(start)s)",
                        person=target,
                        duration=leave.duration_display,
                        start=display_date,
                    )
                else:
                    leave.display_name = _("%(person)s on %(leave_type)s: %(duration)s (%(start)s)",
                        person=target,
                        leave_type=time_off_type_display,
                        duration=leave.duration_display,
                        start=display_date,
                    )
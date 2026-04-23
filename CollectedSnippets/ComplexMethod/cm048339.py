def _cron_auto_check_out(self):
        def check_in_tz(attendance):
            """Returns check-in time in calendar's timezone."""
            return attendance.check_in.astimezone(pytz.timezone(attendance.employee_id._get_tz()))

        to_verify = self.env['hr.attendance'].search(
            [('check_out', '=', False),
             ('employee_id.company_id.auto_check_out', '=', True),
             ('employee_id.resource_calendar_id.flexible_hours', '=', False)]
        )

        if not to_verify:
            return

        to_verify_min_date = min(to_verify.mapped('check_in')).replace(hour=0, minute=0, second=0)
        previous_attendances = self.env['hr.attendance'].search([
                    ('employee_id', 'in', to_verify.mapped('employee_id').ids),
                    ('check_in', '>', to_verify_min_date),
                    ('check_out', '!=', False)
        ])

        mapped_previous_duration = defaultdict(lambda: defaultdict(float))
        for previous in previous_attendances:
            mapped_previous_duration[previous.employee_id][check_in_tz(previous).date()] += previous.worked_hours

        all_companies = to_verify.employee_id.company_id

        for company in all_companies:
            max_tol = company.auto_check_out_tolerance
            to_verify_company = to_verify.filtered(lambda a: a.employee_id.company_id.id == company.id)

            for att in to_verify_company:

                employee_timezone = pytz.timezone(att.employee_id._get_tz())
                check_in_datetime = check_in_tz(att)
                now_datetime = fields.Datetime.now().astimezone(employee_timezone)
                current_attendance_duration = (now_datetime - check_in_datetime).total_seconds() / 3600
                previous_attendances_duration = mapped_previous_duration[att.employee_id][check_in_datetime.date()]

                expected_worked_hours = sum(
                    att.employee_id.resource_calendar_id.attendance_ids.filtered(
                        lambda a: a.dayofweek == str(check_in_datetime.weekday())
                            and (not a.two_weeks_calendar or a.week_type == str(a.get_week_type(check_in_datetime.date())))
                    ).mapped("duration_hours")
                )

                # Attendances where Last open attendance time + previously worked time on that day + tolerance greater than the attendances hours (including lunch) in his calendar
                if (current_attendance_duration + previous_attendances_duration - max_tol) > expected_worked_hours:
                    att.check_out = att.check_in.replace(hour=23, minute=59, second=59)
                    excess_hours = att.worked_hours - (expected_worked_hours + max_tol - previous_attendances_duration)
                    att.write({
                        "check_out": max(att.check_out - relativedelta(hours=excess_hours), att.check_in + relativedelta(seconds=1)),
                        "out_mode": "auto_check_out"
                    })
                    att.message_post(
                        body=_('This attendance was automatically checked out because the employee exceeded the allowed time for their scheduled work hours.')
                    )
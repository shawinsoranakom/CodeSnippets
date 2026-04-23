def _update_overtime(self, attendance_domain=None):
        if not attendance_domain:
            attendance_domain = self._get_overtimes_to_update_domain()
        all_overtime_lines = self.env['hr.attendance.overtime.line'].search(attendance_domain)
        manual_overtimes = set(all_overtime_lines.filtered(
            lambda l: l.manual_duration != l.duration or l.status == 'to_approve'
        ).mapped(lambda l: (l.employee_id.id, l.date)))
        all_overtime_lines.unlink()
        all_attendances = (self | self.env['hr.attendance'].search(attendance_domain)).filtered_domain([('check_out', '!=', False)])
        if not all_attendances:
            return

        start_check_in = min(all_attendances.mapped('check_in')).date() - relativedelta(days=1)  # for timezone
        min_check_in = utc.localize(datetime.combine(start_check_in, datetime.min.time()))

        start_check_out = max(all_attendances.mapped('check_out')).date() + relativedelta(days=1)
        max_check_out = utc.localize(datetime.combine(start_check_out, datetime.max.time()))  # for timezone

        version_periods_by_employee = all_attendances.employee_id.sudo()._get_version_periods(min_check_in, max_check_out)
        attendances_by_employee = all_attendances.grouped('employee_id')
        attendances_by_ruleset = defaultdict(lambda: self.env['hr.attendance'])
        for employee, emp_attendance in attendances_by_employee.items():
            for attendance in emp_attendance:
                version_sudo = employee.sudo()._get_version(attendance._get_localized_times()[0])
                ruleset_sudo = version_sudo.ruleset_id
                if ruleset_sudo:
                    attendances_by_ruleset[ruleset_sudo] += attendance
        employees = all_attendances.employee_id
        schedules_intervals_by_employee = employees._get_schedules_by_employee_by_work_type(min_check_in, max_check_out, version_periods_by_employee)
        overtime_vals_list = []
        for ruleset_sudo, ruleset_attendances in attendances_by_ruleset.items():
            attendances_dates = list(chain(*ruleset_attendances._get_dates().values()))
            overtime_vals_list.extend([
                {
                    **val,
                    'status': 'to_approve'
                } if (val['employee_id'], val['date']) in manual_overtimes else val
                for val in ruleset_sudo.rule_ids._generate_overtime_vals_v2(min(attendances_dates), max(attendances_dates), ruleset_attendances, schedules_intervals_by_employee)
            ])
        self.env['hr.attendance.overtime.line'].create(overtime_vals_list)
        self.env.add_to_compute(self._fields['overtime_hours'], all_attendances)
        self.env.add_to_compute(self._fields['expected_hours'], all_attendances)
        self.env.add_to_compute(self._fields['validated_overtime_hours'], all_attendances)
        self.env.add_to_compute(self._fields['overtime_status'], all_attendances)
def _check_validity(self):
        sorted_leaves = defaultdict(lambda: self.env['hr.leave'])
        for leave in self:
            sorted_leaves[(leave.holiday_status_id, leave.date_from.date())] |= leave
        for (leave_type, date_from), leaves in sorted_leaves.items():
            if not leave_type.requires_allocation:
                continue
            employees = leaves.employee_id
            leave_data = leave_type.get_allocation_data(employees, date_from)
            if leave_type.allows_negative:
                max_excess = leave_type.max_allowed_negative
                is_cancellation = all(leave.state in ('cancel', 'refuse') for leave in leaves)
                for employee in employees:
                    if is_cancellation:
                        continue
                    if not leave_data[employee][0][1]['max_leaves']:
                        raise ValidationError(_("You do not have any allocation for this time off type.\n"
                                                "Please request an allocation before submitting your time off request."))
                    if leave_data[employee] and leave_data[employee][0][1]['virtual_remaining_leaves'] < -max_excess:
                        raise ValidationError(_("There is no valid allocation to cover that request."))
                continue

            previous_leave_data = leave_type.with_context(
                ignored_leave_ids=leaves.ids
            ).get_allocation_data(employees, date_from)
            for employee in employees:
                previous_emp_data = previous_leave_data[employee] and previous_leave_data[employee][0][1]['virtual_excess_data']
                emp_data = leave_data[employee] and leave_data[employee][0][1]['virtual_excess_data']
                if not leave_data[employee][0][1]['max_leaves']:
                    raise ValidationError(_("You do not have any allocation for this time off type.\n"
                                            "Please request an allocation before submitting your time off request."))
                if not previous_emp_data and not emp_data:
                    continue
                if previous_emp_data != emp_data and len(emp_data) >= len(previous_emp_data):
                    raise ValidationError(_("There is no valid allocation to cover that request."))
        is_leave_user = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        if not is_leave_user and any(leave.has_mandatory_day for leave in self):
            raise ValidationError(_('You are not allowed to request time off on a Mandatory Day'))
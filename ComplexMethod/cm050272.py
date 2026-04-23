def _compute_presence_state(self):
        """
        This method is overritten in several other modules which add additional
        presence criterions. e.g. hr_attendance, hr_holidays
        """
        # sudo: res.users - can access presence of accessible user
        employee_to_check_working = self.filtered(
            lambda e: (e.user_id.sudo().presence_ids.status or "offline") == "offline"
        )
        working_now_list = employee_to_check_working._get_employee_working_now()
        for employee in self:
            state = 'out_of_working_hour'
            if employee.company_id.sudo().hr_presence_control_login:
                # sudo: res.users - can access presence of accessible user
                presence_status = employee.user_id.sudo().presence_ids.status or "offline"
                if presence_status == "online":
                    state = 'present'
                elif presence_status == "offline" and employee.id in working_now_list:
                    state = 'absent'
            if not employee.active:
                state = 'archive'
            employee.hr_presence_state = state
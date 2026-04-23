def _compute_from_employee_id(self):
        for holiday in self:
            if not holiday.holiday_status_id.requires_allocation:
                continue
            if not holiday.employee_id:
                holiday.holiday_status_id = False
            elif holiday.employee_id.user_id != self.env.user and holiday._origin.employee_id != holiday.employee_id:
                if holiday.employee_id and not holiday.holiday_status_id.with_context(employee_id=holiday.employee_id.id).has_valid_allocation:
                    holiday.holiday_status_id = False
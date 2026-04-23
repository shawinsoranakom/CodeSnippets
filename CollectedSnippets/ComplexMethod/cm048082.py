def _compute_allocation_remaining_display(self):
        current_date = date.today()
        allocations = self.env['hr.leave.allocation'].search([('employee_id', 'in', self.ids)])
        leaves_taken = self._get_consumed_leaves(allocations.holiday_status_id)[0]
        for employee in self:
            employee_remaining_leaves = 0
            employee_max_leaves = 0
            for leave_type in leaves_taken[employee]:
                if leave_type.requires_allocation == 'no' or leave_type.hide_on_dashboard or not leave_type.active:
                    continue
                for allocation in leaves_taken[employee][leave_type]:
                    if allocation and allocation.date_from <= current_date\
                            and (not allocation.date_to or allocation.date_to >= current_date):
                        virtual_remaining_leaves = leaves_taken[employee][leave_type][allocation]['virtual_remaining_leaves']
                        employee_remaining_leaves += virtual_remaining_leaves\
                            if leave_type.request_unit in ['day', 'half_day']\
                            else virtual_remaining_leaves / (employee.resource_calendar_id.hours_per_day or HOURS_PER_DAY)
                        employee_max_leaves += allocation.number_of_days
            employee.allocation_remaining_display = "%g" % float_round(employee_remaining_leaves, precision_digits=2)
            employee.allocation_display = "%g" % float_round(employee_max_leaves, precision_digits=2)
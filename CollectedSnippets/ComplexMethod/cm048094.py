def write(self, vals):
        values = vals
        employee_id = values.get('employee_id', False)
        if values.get('state'):
            self._check_approval_update(values['state'])

        self.add_follower(employee_id)

        if 'number_of_days_display' not in values and 'number_of_hours_display' not in values and 'state' not in values:
            res = super().write(values)
            if 'allocation_type' in values:
                self._add_lastcalls()
            return res

        previous_consumed_leaves = self.employee_id._get_consumed_leaves(leave_types=self.holiday_status_id)
        result = super().write(values)
        consumed_leaves = self.employee_id._get_consumed_leaves(leave_types=self.holiday_status_id)

        if 'allocation_type' in values:
            self._add_lastcalls()
        for allocation in self:
            current_excess = dict(consumed_leaves[1]).get(allocation.employee_id, {}) \
                .get(allocation.holiday_status_id, {}).get('excess_days', {})
            previous_excess = dict(previous_consumed_leaves[1]).get(allocation.employee_id, {}) \
                .get(allocation.holiday_status_id, {}).get('excess_days', {})
            total_current_excess = sum(leave_date['amount'] for leave_date in current_excess.values() if not leave_date['is_virtual'])
            total_previous_excess = sum(leave_date['amount'] for leave_date in previous_excess.values() if not leave_date['is_virtual'])

            if total_current_excess <= total_previous_excess:
                continue
            lt = allocation.holiday_status_id
            if lt.allows_negative and total_current_excess <= lt.max_allowed_negative:
                continue
            raise ValidationError(
                _('You cannot reduce the duration below the duration of leaves already taken by the employee.'))

        return result
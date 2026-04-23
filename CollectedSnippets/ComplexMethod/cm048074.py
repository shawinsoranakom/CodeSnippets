def _get_next_states_by_state(self):
        self.ensure_one()
        state_result = {
            'confirm': set(),
            'validate1': set(),
            'validate': set(),
            'refuse': set(),
            'cancel': set()
        }
        validation_type = self.validation_type

        user_employees = self.env.user.employee_ids
        is_own_leave = self.employee_id in user_employees
        is_in_past = self.date_from and self.date_from.date() < fields.Date.today()

        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_time_off_manager = self.employee_id.leave_manager_id == self.env.user

        if is_own_leave and (not is_in_past or is_officer):
            state_result['validate1'].add('cancel')
            state_result['validate'].add('cancel')
            state_result['refuse'].add('cancel')

        if is_officer:
            if validation_type == 'both':
                state_result['confirm'].add('validate1')
                state_result['refuse'].add('validate1')
                state_result['cancel'].add('validate1')
            state_result['confirm'].update({'validate', 'refuse'})
            state_result['validate1'].update({'confirm', 'validate', 'refuse'})
            state_result['validate'].update({'confirm', 'refuse'})
            state_result['refuse'].update({'confirm', 'validate'})
            state_result['cancel'].update({'confirm', 'validate', 'refuse'})
        elif is_time_off_manager:
            if validation_type != 'hr':
                state_result['confirm'].add('refuse')
                state_result['validate'].add('refuse')
            if validation_type == 'both':
                state_result['confirm'].add('validate1')
                state_result['validate1'].add('refuse')
            elif validation_type == 'manager':
                state_result['confirm'].add('validate')
                state_result['refuse'].add('validate')

        return state_result
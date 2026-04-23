def _get_next_states_by_state(self):
        self.ensure_one()
        state_result = {
            'confirm': set(),
            'validate1': set(),
            'validate': set(),
            'refuse': set(),
        }
        validation_type = self.validation_type

        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_time_off_manager = self.employee_id.leave_manager_id == self.env.user

        if is_officer:
            if validation_type == 'both':
                state_result['confirm'].add('validate1')
                state_result['refuse'].add('validate1')
            state_result['validate1'].update({'confirm', 'validate', 'refuse'})
            state_result['confirm'].update({'validate', 'refuse'})
            state_result['validate'].update({'confirm', 'refuse'})
            state_result['refuse'].update({'confirm', 'validate'})
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

        if validation_type == 'no_validation':
            state_result['confirm'].add('validate')
        return state_result
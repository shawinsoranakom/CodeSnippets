def _check_approval_update(self, state, raise_if_not_possible=True):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return True

        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')

        for holiday in self:
            is_time_off_manager = holiday.employee_id.leave_manager_id == self.env.user
            dict_all_possible_state = holiday._get_next_states_by_state()
            validation_type = holiday.validation_type
            error_message = ""
            # Standard Check
            if holiday.state == state:
                error_message = self.env._('You can\'t do the same action twice.')
            elif state == 'validate1' and validation_type != 'both':
                error_message = self.env._('Not possible state. State Approve is only used for leave needed 2 approvals')
            elif holiday.state == 'cancel':
                error_message = self.env._('A cancelled leave cannot be modified.')
            elif state not in dict_all_possible_state.get(holiday.state, {}):
                if state == 'cancel':
                    error_message = self.env._('You can only cancel your own leave. You can cancel a leave only if this leave \
is approved, validated or refused.')
                elif state == 'confirm':
                    error_message = self.env._('You can\'t reset a leave. Cancel/delete this one and create an other')
                elif state == 'validate1':
                    if not is_time_off_manager:
                        error_message = self.env._('Only a Time Off Officer/Manager can approve a leave.')
                    else:
                        error_message = self.env._('You can\'t approve a validated leave.')
                elif state == "validate":
                    if not is_time_off_manager:
                        error_message = self.env._('Only a Time Off Officer/Manager can validate a leave.')
                    elif holiday.state == "refuse":
                        error_message = self.env._('You can\'t approve this refused leave.')
                    else:
                        error_message = self.env._('You can only validate a leave with validation by Time Off Manager.')
                elif state == "refuse":
                    if not is_time_off_manager:
                        error_message = self.env._('Only a Time Off Officer/Manager can refuse a leave.')
                    else:
                        error_message = self.env._('You can\'t refuse a leave with validation by Time Off Officer.')
            elif state != "cancel":
                try:
                    holiday.check_access('write')
                except UserError as e:
                    if raise_if_not_possible:
                        raise UserError(e)
                    return False
                else:
                    continue
            if error_message:
                if raise_if_not_possible:
                    raise UserError(error_message)
                return False
        return True
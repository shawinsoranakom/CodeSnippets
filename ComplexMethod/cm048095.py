def _check_approval_update(self, state, raise_if_not_possible=True):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return True
        current_employee = self.env.user.employee_id
        is_administrator = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        for allocation in self:
            is_time_off_manager = allocation.employee_id.leave_manager_id == self.env.user
            error_message = ""
            dict_all_possible_state = allocation._get_next_states_by_state()
            if allocation.state == state:
                error_message = _('You can\'t do the same action twice.')
            elif allocation.employee_id == current_employee and \
                allocation.holiday_status_id.allocation_validation_type != 'no_validation' and not is_administrator:
                error_message = _('Only a time off Administrator can approve/refuse their own requests.')
            elif state not in dict_all_possible_state.get(allocation.state, {}):
                if state == 'confirm':
                    error_message = _('You can\'t reset an allocation. Cancel/delete this one and create an other')
                elif state == 'validate1':
                    if not is_time_off_manager:
                        error_message = _('Only a Time Off Officer/Manager can approve an allocation.')
                    else:
                        error_message = _('You can\'t approve a validated allocation.')
                elif state == 'validate':
                    if not is_time_off_manager:
                        error_message = _('Only a Time Off Officer/Manager can validate an allocation.')
                    elif allocation.state == "refuse":
                        error_message = _('You can\'t approve this refused allocation.')
                    else:
                        error_message = _('You can only validate an allocation with validation by Time Off Manager.')
                elif state == "refuse":
                    if not is_time_off_manager:
                        error_message = _('Only a Time Off Officer/Manager can refuse an allocation.')
                    else:
                        error_message = _('You can\'t refuse an allocation with validation by Time Off Officer.')
                else:
                    try:
                        allocation.check_access('write')
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
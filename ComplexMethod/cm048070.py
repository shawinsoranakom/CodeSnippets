def action_approve(self, check_state=True):
        current_employee = self.env.user.employee_id
        leave_to_approve = self.env['hr.leave']
        leave_to_validate = self.env['hr.leave']
        for leave in self:
            if check_state and leave.can_validate or not check_state and leave.validation_type != "both":
                leave_to_validate += leave
            elif check_state and leave.can_approve or not check_state and leave.validation_type == 'both':
                leave_to_approve += leave
            else:
                raise UserError(self.env._('You cannot approve this leave.'))
        leave_to_approve.write({'state': 'validate1', 'first_approver_id': current_employee.id})
        leave_to_validate._action_validate(check_state)
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        return True
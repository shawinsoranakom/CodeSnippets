def activity_update(self):
        to_clean, to_do, to_second_do = self.env['hr.leave.allocation'], self.env['hr.leave.allocation'], self.env['hr.leave.allocation']
        activity_vals = []
        model_id = self.env['ir.model']._get_id('hr.leave.allocation')
        confirm_activity = self.env.ref('hr_holidays.mail_act_leave_allocation_approval')
        approval_activity = self.env.ref('hr_holidays.mail_act_leave_allocation_second_approval')
        for allocation in self:
            if allocation.state in ['confirm', 'validate1']:
                if allocation.holiday_status_id.leave_validation_type != 'no_validation':
                    if allocation.state == 'confirm':
                        activity_type = confirm_activity
                        note = _(
                            'New Allocation Request created by %(user)s: %(count)s Days of %(allocation_type)s',
                            user=allocation.create_uid.name,
                            count=float_round(allocation.number_of_days, precision_digits=2),
                            allocation_type=allocation.holiday_status_id.name,
                        )
                    else:
                        activity_type = approval_activity
                        note = _(
                            'Second approval request for %(allocation_type)s',
                            allocation_type=allocation.holiday_status_id.name,
                        )
                        to_second_do |= allocation
                    user_ids = allocation.sudo()._get_responsible_for_approval().ids
                    for user_id in user_ids:
                        activity_vals.append({
                            'activity_type_id': activity_type.id,
                            'automated': True,
                            'note': note,
                            'user_id': user_id,
                            'res_id': allocation.id,
                            'res_model_id': model_id,
                        })
            elif allocation.state == 'validate':
                to_do |= allocation

            elif allocation.state == 'refuse':
                to_clean |= allocation

        if to_clean:
            to_clean.activity_unlink(['hr_holidays.mail_act_leave_allocation_approval'])
        if to_do:
            to_do.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval', 'hr_holidays.mail_act_leave_allocation_second_approval'])
        if to_second_do:
            to_second_do.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval'])

        if activity_vals:
            self.env['mail.activity'].create(activity_vals)
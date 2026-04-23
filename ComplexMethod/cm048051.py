def _reevaluate_leaves(self, time_domain_dict):
        if not time_domain_dict:
            return

        domain = self._get_domain(time_domain_dict)
        leaves = self.env['hr.leave'].search(domain)
        if not leaves:
            return

        previous_durations = leaves.mapped('number_of_days')
        previous_states = leaves.mapped('state')
        self.env.add_to_compute(self.env['hr.leave']._fields['number_of_days'], leaves)
        self.env.add_to_compute(self.env['hr.leave']._fields['duration_display'], leaves)
        leaves.sudo().write({
            'state': 'confirm',
        })
        sick_time_status = self.env.ref('hr_holidays.leave_type_sick_time_off', raise_if_not_found=False)
        leaves_to_recreate = self.env['hr.leave']
        for previous_duration, leave, state in zip(previous_durations, leaves, previous_states):
            duration_difference = previous_duration - leave.number_of_days
            message = False
            if duration_difference > 0 and leave.holiday_status_id.requires_allocation:
                message = _("Due to a change in global time offs, you have been granted %s day(s) back.", duration_difference)
            if leave.number_of_days > previous_duration\
                    and (not sick_time_status or leave.holiday_status_id not in sick_time_status):
                message = _("Due to a change in global time offs, %s extra day(s) have been taken from your allocation. Please review this leave if you need it to be changed.", -1 * duration_difference)
            try:
                leave.sudo().write({'state': state})  # sudo in order to skip _check_approval_update
                leave._check_validity()
                if leave.state == 'validate':
                    # recreate the resource leave that were removed by writing state to draft
                    leaves_to_recreate |= leave
            except ValidationError:
                leave.action_refuse()
                message = _("Due to a change in global time offs, this leave no longer has the required amount of available allocation and has been set to refused. Please review this leave.")
            if message:
                leave._notify_change(message)
        leaves_to_recreate.sudo()._create_resource_leave()
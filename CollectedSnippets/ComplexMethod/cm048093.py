def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        for values in vals_list:
            if 'state' in values and values['state'] != 'confirm':
                raise UserError(_('Incorrect state for new allocation'))
            employee_id = values.get('employee_id', False)
            if not values.get('department_id'):
                values.update({'department_id': self.env['hr.employee'].sudo().browse(employee_id).department_id.id})
        allocations = super(HrLeaveAllocation, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        allocations._add_lastcalls()
        for allocation in allocations:
            partners_to_subscribe = set()
            if allocation.employee_id.user_id:
                partners_to_subscribe.add(allocation.employee_id.user_id.partner_id.id)
            if allocation.validation_type == 'hr':
                partners_to_subscribe.add(allocation.employee_id.sudo().parent_id.user_id.partner_id.id)
                partners_to_subscribe.add(allocation.employee_id.leave_manager_id.partner_id.id)
            allocation.message_subscribe(partner_ids=tuple(partners_to_subscribe))
            if not self.env.context.get('import_file'):
                allocation.activity_update()
            if allocation.validation_type == 'no_validation' and allocation.state == 'confirm':
                allocation.action_approve()
        return allocations
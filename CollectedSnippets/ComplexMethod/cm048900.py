def write(self, vals):
        partner_ids = []
        # subscribe employee or department manager when equipment assign to employee or department.
        if vals.get('employee_id'):
            user_id = self.env['hr.employee'].browse(vals['employee_id'])['user_id']
            if user_id:
                partner_ids.append(user_id.partner_id.id)
        if vals.get('department_id'):
            department = self.env['hr.department'].browse(vals['department_id'])
            if department and department.manager_id and department.manager_id.user_id:
                partner_ids.append(department.manager_id.user_id.partner_id.id)
        if partner_ids:
            self.message_subscribe(partner_ids=partner_ids)
        return super(MaintenanceEquipment, self).write(vals)
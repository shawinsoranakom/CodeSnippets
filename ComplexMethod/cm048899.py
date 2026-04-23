def create(self, vals_list):
        equipments = super().create(vals_list)
        for equipment in equipments:
            # TDE FIXME: check if we can use suggested recipients for employee and department manager
            # subscribe employee or department manager when equipment assign to him.
            partner_ids = []
            if equipment.employee_id and equipment.employee_id.user_id:
                partner_ids.append(equipment.employee_id.user_id.partner_id.id)
            if equipment.department_id and equipment.department_id.manager_id and equipment.department_id.manager_id.user_id:
                partner_ids.append(equipment.department_id.manager_id.user_id.partner_id.id)
            if partner_ids:
                equipment.message_subscribe(partner_ids=partner_ids)
        return equipments
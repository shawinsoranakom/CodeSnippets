def set_values(self):
        routing_before = self.env.user.has_group('mrp.group_mrp_routings')
        super().set_values()
        if routing_before and not self.group_mrp_routings:
            self.env['mrp.routing.workcenter'].search([]).active = False
        elif not routing_before and self.group_mrp_routings:
            operations = self.env['mrp.routing.workcenter'].search_read([('active', '=', False)], ['id', 'write_date'])
            last_updated = max((op['write_date'] for op in operations), default=0)
            if last_updated:
                op_to_update = self.env['mrp.routing.workcenter'].browse([op['id'] for op in operations if op['write_date'] == last_updated])
                op_to_update.active = True
        if not self.group_mrp_workorder_dependencies:
            # Disabling this option should not interfere with currently planned productions
            self.env['mrp.bom'].sudo().search([('allow_operation_dependencies', '=', True)]).allow_operation_dependencies = False
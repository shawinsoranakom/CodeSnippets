def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        allocated_hours = 0.0
        if self.product_id.service_type != 'milestones':
            allocated_hours = self._convert_qty_company_hours(self.company_id)
        sale_line_name_parts = self.name.split('\n')

        if sale_line_name_parts and sale_line_name_parts[0] == self.product_id.display_name:
            sale_line_name_parts.pop(0)

        if len(sale_line_name_parts) == 1 and sale_line_name_parts[0]:
            title = sale_line_name_parts[0]
            description = ''
        else:
            title = self.product_id.display_name
            description = '<br/>'.join(sale_line_name_parts)

        return {
            'name': title if project.sale_line_id else '%s - %s' % (self.order_id.name or '', title),
            'allocated_hours': allocated_hours,
            'partner_id': self.order_id.partner_id.id,
            'description': description,
            'project_id': project.id,
            'sale_line_id': self.id,
            'sale_order_id': self.order_id.id,
            'company_id': project.company_id.id,
            'user_ids': False,  # force non assigned task, as created as sudo()
        }
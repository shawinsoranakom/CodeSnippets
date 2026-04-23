def write(self, vals):
        sols_with_no_qty_ordered = self.env['sale.order.line']
        if 'product_uom_qty' in vals and vals.get('product_uom_qty') > 0:
            sols_with_no_qty_ordered = self.filtered(lambda sol: sol.product_uom_qty == 0)
        result = super().write(vals)
        # changing the ordered quantity should change the allocated hours on the
        # task, whatever the SO state. It will be blocked by the super in case
        # of a locked sale order.
        if vals.get('product_uom_qty') and sols_with_no_qty_ordered:
            sols_with_no_qty_ordered.filtered(lambda l: l.is_service and l.state == 'sale' and not l.is_expense)._timesheet_service_generation()
        if 'product_uom_qty' in vals and not self.env.context.get('no_update_allocated_hours', False):
            for line in self:
                if line.task_id and line.product_id.type == 'service':
                    allocated_hours = line._convert_qty_company_hours(line.task_id.company_id or self.env.user.company_id)
                    line.task_id.write({'allocated_hours': allocated_hours})
        return result
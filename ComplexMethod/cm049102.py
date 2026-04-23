def action_view_timesheet(self):
        self.ensure_one()
        if not self.order_line:
            return {'type': 'ir.actions.act_window_close'}

        action = self.env["ir.actions.actions"]._for_xml_id("sale_timesheet.timesheet_action_from_sales_order")
        default_sale_line = next((sale_line for sale_line in self.order_line if sale_line.is_service and sale_line.product_id.service_policy in ['ordered_prepaid', 'delivered_timesheet']), self.env['sale.order.line'])
        context = {
            'search_default_billable_timesheet': True,
            'default_is_so_line_edited': True,
            'default_so_line': default_sale_line.id,
        }  # erase default filters

        tasks = self.order_line.task_id._filtered_access('write')
        if tasks:
            context['default_task_id'] = tasks[0].id
        else:
            projects = self.order_line.project_id._filtered_access('write')
            if projects:
                context['default_project_id'] = projects[0].id
            elif self.project_ids:
                context['default_project_id'] = self.project_ids[0].id
        action.update({
            'context': context,
            'domain': [('so_line', 'in', self.order_line.ids), ('project_id', '!=', False)],
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    No activities found. Let's start a new one!
                </p><p>
                    Track your working hours by projects every day and invoice this time to your customers.
                </p>
            """)
        })

        return action
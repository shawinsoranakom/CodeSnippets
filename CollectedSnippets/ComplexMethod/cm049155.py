def create(self, vals_list):
        created_records = super().create(vals_list)
        project = self.env['project.project'].browse(self.env.context.get('create_for_project_id'))
        task = self.env['project.task'].browse(self.env.context.get('create_for_task_id'))
        if project or task:
            service_sol = next((sol for sol in created_records.order_line if sol.is_service), self.env['sale.order.line'])
            if project and not project.sale_line_id:
                project.sale_line_id = service_sol
                if not project.reinvoiced_sale_order_id:
                    project.reinvoiced_sale_order_id = service_sol.order_id or created_records[0] if created_records else False
            if task and not task.sale_line_id:
                created_records.with_context(disable_project_task_generation=True).action_confirm()
                task.sale_line_id = service_sol
        return created_records
def _action_confirm(self):
        """ On SO confirmation, some lines should generate a task or a project. """
        if self.env.context.get('disable_project_task_generation'):
            return super()._action_confirm()

        if len(self.company_id) == 1:
            # All orders are in the same company
            self.order_line.sudo().with_company(self.company_id)._timesheet_service_generation()
        else:
            # Orders from different companies are confirmed together
            for order in self:
                order.order_line.sudo().with_company(order.company_id)._timesheet_service_generation()

        # If the order has exactly one project and that project comes from a template, set the company of the template
        # on the project.
        for order in self.sudo(): # Salesman may not have access to projects
            if len(order.project_ids) == 1:
                project = order.project_ids[0]
                for sol in order.order_line:
                    if project == sol.project_id and (project_template := sol.product_template_id.project_template_id):
                        project.sudo().company_id = project_template.sudo().company_id
                        break
        return super()._action_confirm()
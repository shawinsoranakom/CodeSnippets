def create(self, vals_list):
        lines = super().create(vals_list)
        # Do not generate task/project when expense SO line, but allow
        # generate task with hours=0.
        confirmed_lines = lines.filtered(lambda sol: sol.state == 'sale' and not sol.is_expense)
        # We track the lines that already generated a task, so we know we won't have to post a message for them after calling the generation service
        has_task_lines = confirmed_lines.filtered('task_id')
        confirmed_lines.sudo()._timesheet_service_generation()
        # if the SO line created a task, post a message on the order
        for line in confirmed_lines - has_task_lines:
            if line.task_id:
                msg_body = _("Task Created (%(name)s): %(link)s", name=line.product_id.name, link=line.task_id._get_html_link())
                line.order_id.message_post(body=msg_body)

        # Set a service SOL on the project, if any is given
        if project_id := self.env.context.get('link_to_project'):
            assert (service_line := next((line for line in lines if line.is_service), False))
            project = self.env['project.project'].browse(project_id)
            if not project.sale_line_id:
                project.sale_line_id = service_line
                if not project.reinvoiced_sale_order_id:
                    project.reinvoiced_sale_order_id = service_line.order_id
        return lines
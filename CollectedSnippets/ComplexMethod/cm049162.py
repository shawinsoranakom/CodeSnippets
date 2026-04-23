def _timesheet_service_generation(self):
        """ For service lines, create the task or the project. If already exists, it simply links
            the existing one to the line.
            Note: If the SO was confirmed, cancelled, set to draft then confirmed, avoid creating a
            new project/task. This explains the searches on 'sale_line_id' on project/task. This also
            implied if so line of generated task has been modified, we may regenerate it.
        """
        sale_order_lines = self.filtered(
            lambda sol:
                sol.is_service
                and sol.product_id.service_tracking in ['project_only', 'task_in_project', 'task_global_project']
                and not (sol._is_line_optional() and sol.product_uom_qty == 0)
        )
        so_line_task_global_project = sale_order_lines._get_so_lines_task_global_project()
        so_line_new_project = sale_order_lines._get_so_lines_new_project()
        task_templates = self.env['project.task']

        # search so lines from SO of current so lines having their project generated, in order to check if the current one can
        # create its own project, or reuse the one of its order.
        map_so_project = {}
        if so_line_new_project:
            order_ids = self.mapped('order_id').ids
            so_lines_with_project = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.project_template_id', '=', False)])
            map_so_project = {sol.order_id.id: sol.project_id for sol in so_lines_with_project}
            so_lines_with_project_templates = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.project_template_id', '!=', False)])
            map_so_project_templates = {(sol.order_id.id, sol.product_id.project_template_id.id): sol.project_id for sol in so_lines_with_project_templates}

        # search the global project of current SO lines, in which create their task
        map_sol_project = {}
        if so_line_task_global_project:
            map_sol_project = {sol.id: sol.product_id.with_company(sol.company_id).project_id for sol in so_line_task_global_project}

        def _can_create_project(sol):
            if not sol.project_id:
                if sol.product_id.project_template_id:
                    return (sol.order_id.id, sol.product_id.project_template_id.id) not in map_so_project_templates
                elif sol.order_id.id not in map_so_project:
                    return True
            return False

        # we store the reference analytic account per SO
        map_account_per_so = {}

        # project_only, task_in_project: create a new project, based or not on a template (1 per SO). May be create a task too.
        # if 'task_in_project' and project_id configured on SO, use that one instead
        for so_line in so_line_new_project.sorted(lambda sol: (sol.sequence, sol.id)):
            project = False
            if so_line.product_id.service_tracking in ['project_only', 'task_in_project']:
                project = so_line.project_id
            if not project and _can_create_project(so_line):
                # If no reference analytic account exists, set the account of the generated project to the account of the project's SO or create a new one
                account = map_account_per_so.get(so_line.order_id.id)
                if not account:
                    account = so_line.order_id.project_account_id or self.env['account.analytic.account'].create(so_line.order_id._prepare_analytic_account_data())
                    map_account_per_so[so_line.order_id.id] = account
                project = so_line.with_context(project_account_id=account.id)._timesheet_create_project()
                # If the SO generates projects on confirmation and the project's SO is not set, set it to the project's SOL with the lowest (sequence, id)
                if not so_line.order_id.project_id:
                    so_line.order_id.project_id = project
                if so_line.product_id.project_template_id:
                    map_so_project_templates[(so_line.order_id.id, so_line.product_id.project_template_id.id)] = project
                else:
                    map_so_project[so_line.order_id.id] = project
            elif not project:
                # Attach subsequent SO lines to the created project
                so_line.project_id = (
                    map_so_project_templates.get((so_line.order_id.id, so_line.product_id.project_template_id.id))
                    or map_so_project.get(so_line.order_id.id)
                )
            if so_line.product_id.service_tracking == 'task_in_project':
                if not project:
                    if so_line.product_id.project_template_id:
                        project = map_so_project_templates[(so_line.order_id.id, so_line.product_id.project_template_id.id)]
                    else:
                        project = map_so_project[so_line.order_id.id]
                if not so_line.task_id and so_line.product_id.task_template_id not in task_templates:
                    task_templates |= so_line.product_id.task_template_id
                    so_line._timesheet_create_task(project=project)
            so_line._handle_milestones(project)

        # task_global_project: if not set, set the project's SO by looking at global projects
        for so_line in so_line_task_global_project.sorted(lambda sol: (sol.sequence, sol.id)):
            if not so_line.order_id.project_id:
                so_line.order_id.project_id = map_sol_project.get(so_line.id)

        # task_global_project: create task in global projects
        for so_line in so_line_task_global_project:
            if not so_line.task_id:
                project = map_sol_project.get(so_line.id) or so_line.order_id.project_id
                if project and so_line.product_uom_qty > 0:
                    if so_line.product_id.task_template_id not in task_templates:
                        task_templates |= so_line.product_id.task_template_id
                        so_line._timesheet_create_task(project)

                elif not project:
                    raise UserError(_(
                        "A project must be defined on the quotation %(order)s or on the form of products creating a task on order.\n"
                        "The following product need a project in which to put its task: %(product_name)s",
                        order=so_line.order_id.name,
                        product_name=so_line.product_id.name,
                    ))
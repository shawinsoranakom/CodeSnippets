def create(self, vals_list):
        projects = super().create(vals_list)
        sol_ids = set()
        for project, vals in zip(projects, vals_list):
            if (vals.get('sale_line_id')):
                sol_ids.add(vals['sale_line_id'])
            if project.sale_order_id and not project.sale_order_id.project_id:
                project.sale_order_id.project_id = project.id
            elif project.sudo().reinvoiced_sale_order_id and not project.sudo().reinvoiced_sale_order_id.project_id:
                project.sudo().reinvoiced_sale_order_id.project_id = project.id
        if sol_ids:
            projects._ensure_sale_order_linked(list(sol_ids))
        return projects
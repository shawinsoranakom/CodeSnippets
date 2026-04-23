def _compute_sale_line(self):
        for task in self:
            if not (task.allow_billable or task.parent_id.allow_billable):
                task.sale_line_id = False
                continue
            if not task.sale_line_id:
                # if the project_id is set then it means the task is classic task or a subtask with another project than its parent.
                # To determine the sale_line_id, we first need to look at the parent before the project to manage the case of subtasks.
                # Two sub-tasks in the same project do not necessarily have the same sale_line_id (need to look at the parent task).
                sale_line = False
                if task.parent_id.sale_line_id and task.parent_id.partner_id.commercial_partner_id == task.partner_id.commercial_partner_id:
                    sale_line = task.parent_id.sale_line_id
                elif task.milestone_id.sale_line_id:
                    sale_line = task.milestone_id.sale_line_id
                elif task.project_id.sale_line_id and task.project_id.partner_id.commercial_partner_id == task.partner_id.commercial_partner_id:
                    sale_line = task.project_id.sale_line_id
                task.sale_line_id = sale_line
def action_view_subtask_timesheet(self):
        self.ensure_one()
        is_internal_user = self.env.user.has_group('base.group_user')
        task_ids = self.with_context(active_test=False)._get_subtask_ids_per_task_id().get(self.id, [])
        action = self.env["ir.actions.actions"]._for_xml_id("hr_timesheet.timesheet_action_all")
        graph_view_id = self.env.ref("hr_timesheet.view_hr_timesheet_line_graph_by_employee").id
        new_views = []
        for view in action['views']:
            if (not is_internal_user or self.env.context.get('is_project_sharing')) and view[1] not in ['tree', 'kanban', 'form']:
                continue
            if not is_internal_user:
                if view[1] == 'list':
                    tree_view_id = self.env['ir.model.data']._xmlid_to_res_id('hr_timesheet.hr_timesheet_line_portal_tree')
                    if tree_view_id:
                        new_views.insert(0, (tree_view_id, 'list'))
                        continue
                elif view[1] == 'form':
                    form_view_id = self.env['ir.model.data']._xmlid_to_res_id('hr_timesheet.timesheet_view_form_portal_user')
                    if form_view_id:
                        new_views.append((form_view_id, 'form'))
                        continue
                elif view[1] == 'kanban':
                    kanban_view_id = self.env['ir.model.data']._xmlid_to_res_id('hr_timesheet.view_kanban_account_analytic_line_portal_user')
                    if kanban_view_id:
                        new_views.append((kanban_view_id, 'kanban'))
                        continue
            if view[1] == 'graph':
                view = (graph_view_id, 'graph')
            new_views.insert(0, view) if view[1] == 'list' else new_views.append(view)

        action.update({
            'display_name': _('Timesheets'),
            'context': {'default_project_id': self.project_id.id},
            'domain': [('project_id', '!=', False), ('task_id', 'in', task_ids)],
            'views': new_views,
        })
        return action
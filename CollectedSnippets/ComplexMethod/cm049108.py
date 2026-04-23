def action_profitability_items(self, section_name, domain=None, res_id=False):
        self.ensure_one()
        if section_name in ['billable_fixed', 'billable_time', 'billable_milestones', 'billable_manual', 'non_billable']:
            action = self.action_billable_time_button()
            if domain:
                action['domain'] = Domain.AND([[('project_id', '=', self.id)], domain])
            action['context'].update(search_default_groupby_timesheet_invoice_type=False, **self.env.context)
            graph_view = False
            if section_name == 'billable_time':
                graph_view = self.env.ref('sale_timesheet.view_hr_timesheet_line_graph_invoice_employee').id
            action['views'] = [
                (view_id, view_type) if view_type != 'graph' else (graph_view or view_id, view_type)
                for view_id, view_type in action['views']
            ]
            if res_id:
                if 'views' in action:
                    action['views'] = [
                        (view_id, view_type)
                        for view_id, view_type in action['views']
                        if view_type == 'form'
                    ] or [False, 'form']
                action['view_mode'] = 'form'
                action['res_id'] = res_id
            return action
        return super().action_profitability_items(section_name, domain, res_id)
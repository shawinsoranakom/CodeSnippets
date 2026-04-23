def action_profitability_items(self, section_name, domain=None, res_id=False):
        if section_name in ['other_revenues_aal', 'other_costs_aal', 'other_costs']:
            action = self.env["ir.actions.actions"]._for_xml_id("analytic.account_analytic_line_action_entries")
            action['domain'] = domain
            action['context'] = {
                'group_by_date': True,
            }
            if res_id:
                action['views'] = [(False, 'form')]
                action['view_mode'] = 'form'
                action['res_id'] = res_id
            else:
                pivot_view_id = self.env['ir.model.data']._xmlid_to_res_id('project_account.project_view_account_analytic_line_pivot')
                graph_view_id = self.env['ir.model.data']._xmlid_to_res_id('project_account.project_view_account_analytic_line_graph')
                action['views'] = [(pivot_view_id, view_type) if view_type == 'pivot' else (graph_view_id, view_type) if view_type == 'graph' else (view_id, view_type)
                                   for (view_id, view_type) in action['views']]
            return action

        if section_name == 'other_purchase_costs':
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
            action['domain'] = domain or []
            if res_id:
                action['views'] = [(False, 'form')]
                action['view_mode'] = 'form'
                action['res_id'] = res_id
            return action

        return super().action_profitability_items(section_name, domain, res_id)
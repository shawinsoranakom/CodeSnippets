def action_profitability_items(self, section_name, domain=None, res_id=False):
        if section_name in ['service_revenues', 'materials']:
            view_types = ['list', 'kanban', 'form']
            action = {
                'name': _('Sales Order Items'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order.line',
                'context': {'create': False, 'edit': False},
            }
            if res_id:
                action['res_id'] = res_id
                view_types = ['form']
            else:
                action['domain'] = domain
            action['views'] = [(False, v) for v in view_types]
            return action

        if section_name in ['other_invoice_revenues', 'downpayments']:
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
            action['domain'] = domain if domain else []
            action['context'] = {
                **ast.literal_eval(action['context']),
                'default_partner_id': self.partner_id.id,
                'project_id': self.id,
            }
            if res_id:
                action['views'] = [(False, 'form')]
                action['view_mode'] = 'form'
                action['res_id'] = res_id
            return action

        if section_name == 'cost_of_goods_sold':
            action = {
                'name': _('Cost of Goods Sold Items'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move.line',
                'views': [[False, 'list'], [False, 'form']],
                'domain': [('move_id', '=', res_id), ('display_type', '=', 'cogs')],
                'context': {'create': False, 'edit': False},
            }
            return action

        return super().action_profitability_items(section_name, domain, res_id)
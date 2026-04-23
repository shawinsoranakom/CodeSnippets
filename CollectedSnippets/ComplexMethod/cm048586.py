def open_action(self):
        """return action based on type for related journals"""
        self.ensure_one()
        action_name = self._select_action_to_open()

        # Set 'account.' prefix if missing.
        if not action_name.startswith("account."):
            action_name = 'account.%s' % action_name

        action = self.env["ir.actions.act_window"]._for_xml_id(action_name)

        if 'context' in action and isinstance(action['context'], str):
            action_context = ast.literal_eval(action['context'])
        else:
            action_context = action.get('context', {})
        action['context'] = {
            **action_context,
            **self.env.context,
            'default_journal_id': self.id,
        }
        domain_type_field = action['res_model'] == 'account.move.line' and 'move_id.move_type' or 'move_type' # The model can be either account.move or account.move.line

        # Override the domain only if the action was not explicitly specified in order to keep the
        # original action domain.
        if action.get('domain') and isinstance(action['domain'], str):
            action['domain'] = ast.literal_eval(action['domain'] or '[]')
        if not self.env.context.get('action_name'):
            if self.type == 'sale':
                action['domain'] = [(domain_type_field, 'in', ('out_invoice', 'out_refund', 'out_receipt', 'entry'))]
            elif self.type == 'purchase':
                action['domain'] = [(domain_type_field, 'in', ('in_invoice', 'in_refund', 'in_receipt', 'entry'))]

        action['domain'] = (action['domain'] or []) + [('journal_id', '=', self.id)]
        return action
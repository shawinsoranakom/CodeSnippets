def load(self, action_id, context=None):
        if context:
            request.update_context(**context)
        Actions = request.env['ir.actions.actions']
        try:
            action_id = int(action_id)
        except ValueError:
            try:
                if '.' in action_id:
                    action = request.env.ref(action_id)
                    assert action._name.startswith('ir.actions.')
                else:
                    action = Actions.sudo().search([('path', '=', action_id)], limit=1)
                    assert action
                action_id = action.id
            except Exception as exc:
                raise MissingActionError(_("The action “%s” does not exist.", action_id)) from exc

        base_action = Actions.browse([action_id]).sudo().read(['type'])
        if not base_action:
            raise MissingActionError(_("The action “%s” does not exist", action_id))
        action_type = base_action[0]['type']
        if action_type == 'ir.actions.report':
            request.update_context(bin_size=True)
        if action_type == 'ir.actions.act_window':
            result = request.env[action_type].sudo().browse([action_id])._get_action_dict()
            return clean_action(result, env=request.env) if result else False
        result = request.env[action_type].sudo().browse([action_id]).read()
        return clean_action(result[0], env=request.env) if result else False
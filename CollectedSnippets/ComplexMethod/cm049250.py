def get_action(env, path_part):
    """
    Get a ir.actions.actions() given an action typically found in a
    "/odoo"-like url.

    The action can take one of the following forms:
    * "action-" followed by a record id
    * "action-" followed by a xmlid
    * "m-" followed by a model name (act_window's res_model)
    * a dotted model name (act_window's res_model)
    * a path (ir.action's path)
    """
    Actions = env['ir.actions.actions']

    if path_part.startswith('action-'):
        someid = path_part.removeprefix('action-')
        if someid.isdigit():  # record id
            action = Actions.sudo().browse(int(someid)).exists()
        elif '.' in someid:   # xml id
            action = env.ref(someid, False)
            if not action or not action._name.startswith('ir.actions'):
                action = Actions
        else:
            action = Actions
    elif path_part.startswith('m-') or '.' in path_part:
        model = path_part.removeprefix('m-')
        if model in env and not env[model]._abstract:
            action = env['ir.actions.act_window'].sudo().search([
                ('res_model', '=', model)], limit=1)
            if not action:
                action = env['ir.actions.act_window'].new(
                    env[model].get_formview_action()
                )
        else:
            action = Actions
    else:
        action = Actions.sudo().search([('path', '=', path_part)])

    if action and action._name == 'ir.actions.actions':
        action_type = action.read(['type'])[0]['type']
        action = env[action_type].browse(action.id)

    return action
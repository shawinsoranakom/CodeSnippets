def load_breadcrumbs(self, actions):
        results = []
        for idx, action in enumerate(actions):
            record_id = action.get('resId')
            try:
                if action.get('action'):
                    act = self.load(action.get('action'))
                    if act['type'] == 'ir.actions.server':
                        if act['path']:
                            act = request.env['ir.actions.server'].browse(act['id']).run()
                        else:
                            results.append({'error': 'A server action must have a path to be restored'})
                            continue
                    if not act.get('display_name'):
                        act['display_name'] = act['name']
                    # client actions don't have multi-record views, so we can't go further to the next controller
                    if act['type'] == 'ir.actions.client' and idx + 1 < len(actions) and action.get('action') == actions[idx + 1].get('action'):
                        results.append({'error': 'Client actions don\'t have multi-record views'})
                        continue
                    if record_id:
                        # some actions may not have a res_model (e.g. a client action)
                        if record_id == 'new':
                            results.append({'display_name': _("New")})
                        elif act['res_model']:
                            results.append({'display_name': request.env[act['res_model']].browse(record_id).display_name})
                        else:
                            results.append({'display_name': act['display_name']})
                    else:
                        if act.get('res_model') and act['type'] != 'ir.actions.client':
                            request.env[act['res_model']].check_access('read')
                            # action shouldn't be available on its own if it doesn't have multi-record views
                            name = act['display_name'] if any(view[1] != 'form' and view[1] != 'search' for view in act['views']) else None
                        else:
                            name = act['display_name']
                        results.append({'display_name': name})
                elif action.get('model'):
                    Model = request.env[action.get('model')]
                    if record_id:
                        if record_id == 'new':
                            results.append({'display_name': _("New")})
                        else:
                            results.append({'display_name': Model.browse(record_id).display_name})
                    else:
                        # This case cannot be produced by the web client
                        raise BadRequest('Actions with a model should also have a resId')
                else:
                    raise BadRequest('Actions should have either an action (id or path) or a model')
            except (MissingActionError, MissingError, AccessError) as exc:
                results.append({'error': str(exc)})
        return results
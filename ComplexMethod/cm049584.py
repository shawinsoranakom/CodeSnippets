def actions_server(self, path_or_xml_id_or_id, **post):
        ServerActions = request.env['ir.actions.server']
        action = action_id = None

        # find the action_id: either an xml_id, the path, or an ID
        if isinstance(path_or_xml_id_or_id, str) and '.' in path_or_xml_id_or_id:
            action = request.env.ref(path_or_xml_id_or_id, raise_if_not_found=False).sudo()
        if not action:
            action = ServerActions.sudo().search(
                [('website_path', '=', path_or_xml_id_or_id), ('website_published', '=', True)], limit=1)
        if not action:
            try:
                action_id = int(path_or_xml_id_or_id)
                action = ServerActions.sudo().browse(action_id).exists()
            except ValueError:
                pass

        # run it, return only if we got a Response object
        if action:
            if action.state == 'code' and action.website_published:
                # use main session env for execution
                action_res = ServerActions.browse(action.id).run()
                if isinstance(action_res, werkzeug.wrappers.Response):
                    return action_res

        return request.redirect('/')
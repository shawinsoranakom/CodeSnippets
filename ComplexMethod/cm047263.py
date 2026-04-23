def _visible_menu_ids(self, debug=False):
        """ Return the ids of the menu items visible to the user. """
        group_ids = set(self.env.user._get_group_ids())
        if not debug:
            group_ids.discard(self.env['ir.model.data']._xmlid_to_res_id('base.group_no_one', raise_if_not_found=False))

        # retrieve menus with a domain to filter out menus with groups the user does not have.
        # It will be used to determine which ones are visible
        menus = self.with_context({}).search_fetch(
            # Don't use 'any' operator in the domain to avoid ir.rule
            ['|', ('group_ids', '=', False), ('group_ids', 'in', tuple(group_ids))],
            ['parent_id', 'action'], order='id',
        ).sudo()

        # take apart menus that have an action
        action_ids_by_model = defaultdict(list)
        for action in menus.mapped('action'):
            if action:
                action_ids_by_model[action._name].append(action.id)

        MODEL_BY_TYPE = {
            'ir.actions.act_window': 'res_model',
            'ir.actions.report': 'model',
            'ir.actions.server': 'model_name',
        }
        def exists_actions(model_name, action_ids):
            """ Return existing actions and fetch model name field if exists"""
            if model_name not in MODEL_BY_TYPE:
                return self.env[model_name].browse(action_ids).exists()
            records = self.env[model_name].sudo().with_context(active_test=False).search_fetch(
                [('id', 'in', action_ids)], [MODEL_BY_TYPE[model_name]], order='id',
            )
            if model_name == 'ir.actions.server':
                # Because it is computed, `search_fetch` doesn't fill the cache for it
                records.mapped('model_name')
            return records

        existing_actions = {
            action
            for model_name, action_ids in action_ids_by_model.items()
            for action in exists_actions(model_name, action_ids)
        }
        menu_ids = set(menus._ids)
        visible_ids = set()
        access = self.env['ir.model.access']
        # process action menus, check whether their action is allowed
        for menu in menus:
            action = menu.action
            if not action or action not in existing_actions:
                continue
            model_fname = MODEL_BY_TYPE.get(action._name)
            # action[model_fname] has been fetched in batch in `exists_actions`
            if model_fname and not access.check(action[model_fname], 'read', False):
                continue
            # make menu visible, and its folder ancestors, too
            menu_id = menu.id
            while menu_id not in visible_ids and menu_id in menu_ids:
                visible_ids.add(menu_id)
                menu = menu.parent_id
                menu_id =  menu.id

        return frozenset(visible_ids)
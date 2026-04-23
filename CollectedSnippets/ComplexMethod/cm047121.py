def from_action(cls, env: api.Environment, action: dict) -> Form:
        assert action['type'] == 'ir.actions.act_window', \
            f"only window actions are valid, got {action['type']}"
        # ensure the first-requested view is a form view
        if views := action.get('views'):
            assert views[0][1] == 'form', \
                f"the actions dict should have a form as first view, got {views[0][1]}"
            view_id = views[0][0]
        else:
            view_mode = action.get('view_mode', '')
            if not view_mode.startswith('form'):
                raise ValueError(f"The actions dict should have a form first view mode, got {view_mode}")
            view_id = action.get('view_id')
            if view_id and ',' in view_mode:
                raise ValueError(f"A `view_id` is only valid if the action has a single `view_mode`, got {view_mode}")
        context = action.get('context', {})
        if isinstance(context, str):
            context = ast.literal_eval(context)
        record = env[action['res_model']]\
            .with_context(context)\
            .browse(action.get('res_id'))

        return cls(record, view_id)
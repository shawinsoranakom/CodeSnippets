def get_bindings(self, model_name):
        """ Retrieve the list of actions bound to the given model.

           :return: a dict mapping binding types to a list of dict describing
                    actions, where the latter is given by calling the method
                    ``read`` on the action record.
        """
        result = {}
        for action_type, all_actions in self._get_bindings(model_name).items():
            actions = []
            for action in all_actions:
                action = dict(action)
                groups = action.pop('group_ids', None)
                if groups and not any(self.env.user.has_group(ext_id) for ext_id in groups):
                    # the user may not perform this action
                    continue
                res_model = action.pop('res_model', None)
                if res_model and not self.env['ir.model.access'].check(
                    res_model,
                    mode='read',
                    raise_exception=False
                ):
                    # the user won't be able to read records
                    continue
                actions.append(action)
            if actions:
                result[action_type] = actions
        return result
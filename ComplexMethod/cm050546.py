def _copy_embedded_actions_config(self, new_projects, shared_embedded_actions_mapping=None):
        shared_embedded_actions_mapping = shared_embedded_actions_mapping or {}
        embedded_action_configs_per_project = dict(
            self.env['res.users.settings.embedded.action'].sudo()._read_group(
                [('res_id', 'in', self.ids), ('res_model', '=', self._name)],
                ['res_id'],
                ['id:recordset'],
            )
        )
        valid_embedded_action_ids = self.env['ir.embedded.actions'].sudo().search(
            domain=[
                ('parent_res_model', '=', self._name),
                ('user_id', '=', False),
            ],
        ).ids + [False]
        new_embedded_actions_config_vals_list = []
        for project, new_project in zip(self, new_projects):
            configs = embedded_action_configs_per_project.get(project.id, self.env['res.users.settings.embedded.action'])
            config_vals_list = configs.copy_data({'res_id': new_project.id})
            for config_vals in config_vals_list:
                # Apply the mapping of shared embedded actions and filter the visibility and order by excluding the user-specific actions
                if config_vals['embedded_actions_visibility']:
                    embedded_actions_visibility = [
                        shared_embedded_actions_mapping.get(action_id, action_id)
                        for action_id in [False if x == 'false' else int(x) for x in config_vals['embedded_actions_visibility'].split(',')]
                        if action_id in valid_embedded_action_ids
                    ]
                    config_vals['embedded_actions_visibility'] = ','.join('false' if action_id is False else str(action_id) for action_id in embedded_actions_visibility)
                if config_vals['embedded_actions_order']:
                    embedded_actions_order = [
                        shared_embedded_actions_mapping.get(action_id, action_id)
                        for action_id in [False if x == 'false' else int(x) for x in config_vals['embedded_actions_order'].split(',')]
                        if action_id in valid_embedded_action_ids
                    ]
                    config_vals['embedded_actions_order'] = ','.join('false' if action_id is False else str(action_id) for action_id in embedded_actions_order)
                new_embedded_actions_config_vals_list.append(config_vals)
        # sudo is needed to update the user settings for all users using the projects to duplicate
        self.env['res.users.settings.embedded.action'].sudo().create(new_embedded_actions_config_vals_list)
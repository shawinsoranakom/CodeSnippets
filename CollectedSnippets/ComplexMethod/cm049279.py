def _embedded_action_settings_format(self):
        return {
            f'{setting.action_id.id}+{setting.res_id or ""}': {
                'embedded_actions_order': [
                    False if action_id == 'false' else int(action_id) for action_id in setting.embedded_actions_order.split(',')
                ] if setting.embedded_actions_order else [],
                'embedded_actions_visibility': [
                    False if action_id == 'false' else int(action_id) for action_id in setting.embedded_actions_visibility.split(',')
                ] if setting.embedded_actions_visibility else [],
                'embedded_visibility': setting.embedded_visibility,
            }
            for setting in self
        }
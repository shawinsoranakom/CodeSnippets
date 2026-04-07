def settings_to_cmd_args_env(self, settings_dict, parameters=None):
        if parameters is None:
            parameters = []
        settings_dict.setdefault("OPTIONS", {})
        return DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)
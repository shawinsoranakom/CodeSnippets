def settings_to_cmd_args_env(cls, settings_dict, parameters):
        args = [cls.executable_name, settings_dict["NAME"], *parameters]
        return args, None
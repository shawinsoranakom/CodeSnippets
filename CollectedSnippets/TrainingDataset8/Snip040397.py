def mock_config_get_option(name):
        if name in overrides_dict:
            return overrides_dict[name]
        return orig_get_option(name)
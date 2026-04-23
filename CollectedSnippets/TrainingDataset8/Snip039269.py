def get_options_for_section(section):
        if section == "theme":
            return theme_opts
        return config.get_options_for_section(section)
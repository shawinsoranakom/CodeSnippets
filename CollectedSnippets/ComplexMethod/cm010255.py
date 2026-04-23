def _parse_log_settings(settings):
    settings = process_env_var_string_for_windows(settings)

    if settings == "":
        return {}

    if settings == "help":
        raise ValueError(help_message(verbose=False))
    elif settings == "+help":
        raise ValueError(help_message(verbose=True))
    if not _validate_settings(settings):
        raise ValueError(_invalid_settings_err_msg(settings))

    settings = re.sub(r"\s+", "", settings)
    log_names = settings.split(",")

    def get_name_level_pair(name):
        clean_name = name.replace(INCR_VERBOSITY_CHAR, "")
        clean_name = clean_name.replace(DECR_VERBOSITY_CHAR, "")

        if name[0] == INCR_VERBOSITY_CHAR:
            level = logging.DEBUG
        elif name[0] == DECR_VERBOSITY_CHAR:
            level = logging.ERROR
        else:
            level = logging.INFO

        return clean_name, level

    log_state = LogState()

    for name in log_names:
        name, level = get_name_level_pair(name)

        if name == "all":
            name = "torch"

        if log_registry.is_log(name):
            if level is None:
                raise AssertionError("level must not be None for log name")
            log_qnames = log_registry.log_alias_to_log_qnames[name]
            log_state.enable_log(log_qnames, level)
        elif log_registry.is_artifact(name):
            log_state.enable_artifact(name)
        elif _is_valid_module(name):
            # Get the module and all its submodules if it's a package
            found_modules = _get_module_and_submodules(name) or (name,)
            for module_name in found_modules:
                if not _has_registered_parent(module_name):
                    log_registry.register_log(module_name, module_name)
                else:
                    log_registry.register_child_log(module_name)
                log_state.enable_log(module_name, level)
        else:
            raise ValueError(_invalid_settings_err_msg(settings))

    return log_state
def _set_logs(**kwargs) -> None:
        for alias, val in itertools.chain(kwargs.items(), modules.items()):  # type: ignore[union-attr]
            if val is None:
                continue

            if log_registry.is_artifact(alias):
                if not isinstance(val, bool):
                    raise ValueError(
                        f"Expected bool to enable artifact {alias}, received {val}"
                    )

                if val:
                    log_state.enable_artifact(alias)
            elif log_registry.is_log(alias) or alias in log_registry.child_log_qnames:
                if val not in logging._levelToName:
                    raise ValueError(
                        f"Unrecognized log level for log {alias}: {val}, valid level values "
                        f"are: {','.join([str(k) for k in logging._levelToName])}"
                    )

                log_state.enable_log(
                    log_registry.log_alias_to_log_qnames.get(alias, alias), val
                )
            elif _is_valid_module(alias):
                found_modules = _get_module_and_submodules(alias) or (alias,)
                for module_name in found_modules:
                    if not _has_registered_parent(module_name):
                        log_registry.register_log(module_name, module_name)
                    else:
                        log_registry.register_child_log(module_name)
                    log_state.enable_log(
                        log_registry.log_alias_to_log_qnames.get(
                            module_name, module_name
                        ),
                        val,
                    )
            else:
                raise ValueError(
                    f"Unrecognized log or artifact name passed to set_logs: {alias}"
                )

        _init_logs()
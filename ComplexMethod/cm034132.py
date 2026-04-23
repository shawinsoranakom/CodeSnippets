def probe_interpreters_for_module(
    interpreter_paths: _c.Sequence[str],
    module_name: str | None = None,
    *,
    module_names: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> str | None:
    """
    Probes a supplied list of Python interpreters, returning the first one capable of
    importing the named modules. This is useful when attempting to locate a "system
    Python" where OS-packaged utility modules are located.

    FIXME environment description (do we want the utility method and/or stored location?)
    FIXME: describe module_name includes basic
    """
    if env is None:
        env = get_env_with_pythonpath()  # compatibility behavior

    if module_name is not None:
        if module_names:
            raise ValueError("The module_name and module_names arguments are mutually exclusive.")

        module_names = [module_name, 'ansible.module_utils.basic']  # compatibility behavior

    if not module_names:
        raise ValueError("No module names were specified.")

    modules_string = ", ".join(module_names)
    for interpreter_path in interpreter_paths:
        if not os.path.exists(interpreter_path):
            continue
        try:
            rc = subprocess.call(
                [
                    interpreter_path,
                    '-c',
                    f'import {modules_string}',
                ],
                env=env,
            )
            if rc == 0:
                return interpreter_path
        except Exception:
            continue

    return None
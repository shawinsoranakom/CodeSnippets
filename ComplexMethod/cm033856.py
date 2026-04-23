def modify_module(
        *,
        module_name: str,
        module_path,
        module_args,
        templar,
        task_vars=None,
        module_compression='ZIP_STORED',
        async_timeout=0,
        become_plugin=None,
        environment=None,
        remote_is_local=False,
        shell_plugin=None,
) -> _BuiltModule:
    """
    Used to insert chunks of code into modules before transfer rather than
    doing regular python imports.  This allows for more efficient transfer in
    a non-bootstrapping scenario by not moving extra files over the wire and
    also takes care of embedding arguments in the transferred modules.

    This version is done in such a way that local imports can still be
    used in the module code, so IDEs don't have to be aware of what is going on.

    Example:

    from ansible.module_utils.basic import *

       ... will result in the insertion of basic.py into the module
       from the module_utils/ directory in the source tree.

    For powershell, this code effectively no-ops, as the exec wrapper requires access to a number of
    properties not available here.

    """
    task_vars = {} if task_vars is None else task_vars
    environment = {} if environment is None else environment
    platform: t.Literal["posix", "windows"] = "windows" if getattr(shell_plugin, "_IS_WINDOWS", False) else "posix"

    # For backwards compatibility and to make it easy for module authors to
    # distinguish between pwsh versions for 5.1 or 7.x we default #!powershell
    # to be powershell and #!/usr/bin/pwsh to pwsh on Windows. Linux only has
    # pwsh 7 and the shebang path works as normal.
    default_interpreters = {
        'powershell': 'powershell' if platform == "windows" else '/usr/bin/pwsh',
        '/usr/bin/pwsh': 'pwsh' if platform == "windows" else '/usr/bin/pwsh',
    }

    with open(module_path, 'rb') as f:

        # read in the module source
        b_module_data = f.read()

    module_bits = _find_module_utils(
        module_name=module_name,
        b_module_data=b_module_data,
        module_path=module_path,
        module_args=module_args,
        task_vars=task_vars,
        templar=templar,
        module_compression=module_compression,
        async_timeout=async_timeout,
        become_plugin=become_plugin,
        environment=environment,
        remote_is_local=remote_is_local,
        platform=platform,
        default_interpreters=default_interpreters,
    )

    if module_bits.b_module_data:
        b_module_data = module_bits.b_module_data
    shebang = module_bits.shebang

    if shebang is None and module_bits.module_style != 'binary':
        interpreter, args = _extract_interpreter(b_module_data)
        # No interpreter/shebang, assume a binary module?
        if interpreter is not None:

            shebang, new_interpreter = _get_shebang(
                interpreter,
                task_vars,
                templar,
                args,
                remote_is_local=remote_is_local,
                default_interpreters=default_interpreters,
            )

            # update shebang
            b_lines = b_module_data.split(b"\n", 1)

            if interpreter != new_interpreter:
                b_lines[0] = to_bytes(shebang, errors='surrogate_or_strict', nonstring='passthru')

            b_module_data = b"\n".join(b_lines)

            module_bits = dataclasses.replace(module_bits, b_module_data=b_module_data, shebang=shebang)

    return module_bits
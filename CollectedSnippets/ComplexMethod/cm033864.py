def _create_powershell_wrapper(
    *,
    name: str,
    module_data: bytes,
    module_path: str,
    module_args: dict[t.Any, t.Any],
    environment: dict[str, str],
    async_timeout: int,
    become_plugin: BecomeBase | None,
    substyle: t.Literal["powershell", "script"],
    task_vars: dict[str, t.Any],
    profile: str,
    pwsh_interpreter: str | None = None,
) -> bytes:
    """Creates module or script wrapper for PowerShell.

    Creates the input data to provide to bootstrap_wrapper.ps1 when running a
    PowerShell module or script.

    :param name: The fully qualified name of the module or script filename (without extension).
    :param module_data: The data of the module or script.
    :param module_path: The path of the module or script.
    :param module_args: The arguments to pass to the module or script.
    :param environment: The environment variables to set when running the module or script.
    :param async_timeout: The timeout to use for async execution or 0 for no async.
    :param become_plugin: The become plugin to use for privilege escalation or None for no become.
    :param substyle: The substyle of the module or script to run [powershell or script].
    :param task_vars: The task variables used on the task.
    :param pwsh_interpreter: The pwsh interpreter to use.

    :return: The input data for bootstrap_wrapper.ps1 as a byte string.
    """

    actions: list[_ManifestAction] = []
    finder = PSModuleDepFinder()
    finder.scan_exec_script('module_wrapper.ps1')

    ext = os.path.splitext(module_path)[1]
    name_with_ext = f"{name}{ext}"
    finder.scripts[name_with_ext] = _ScriptInfo(
        content=module_data,
        path=module_path,
    )

    module_params: dict[str, t.Any] = {
        'Script': name_with_ext,
        'Environment': environment,
    }
    if substyle != 'script':
        module_deps = finder.scan_module(
            module_data,
            fqn=name,
            powershell=True,
        )
        cs_deps = []
        ps_deps = []
        for dep in module_deps:
            if dep.endswith('.cs'):
                cs_deps.append(dep)
            else:
                ps_deps.append(dep)

        module_params |= {
            'Variables': [
                {
                    'Name': 'complex_args',
                    'Value': _prepare_module_args(module_args, profile),
                    'Scope': 'Global',
                },
            ],
            'CSharpModules': cs_deps,
            'PowerShellModules': ps_deps,
            'ForModule': True,
        }

    if become_plugin or finder.become:
        become_script = 'become_wrapper.ps1'
        become_params: dict[str, t.Any] = {
            'BecomeUser': 'SYSTEM',
        }
        become_secure_params: dict[str, t.Any] = {}

        if become_plugin:
            if not isinstance(become_plugin, RunasBecomeModule):
                msg = f"Become plugin {become_plugin.name} is not supported by the Windows exec wrapper. Make sure to set the become method to runas."
                raise AnsibleError(msg)

            become_script, become_params, become_secure_params = become_plugin._build_powershell_wrapper_action()

        finder.scan_exec_script('exec_wrapper.ps1')
        finder.scan_exec_script(become_script)
        actions.append(
            _ManifestAction(
                name=become_script,
                params=become_params,
                secure_params=become_secure_params,
            )
        )

    if async_timeout > 0:
        finder.scan_exec_script('bootstrap_wrapper.ps1')
        finder.scan_exec_script('exec_wrapper.ps1')

        async_dir = environment.get('ANSIBLE_ASYNC_DIR', None)
        if not async_dir:
            raise AnsibleError("The environment variable 'ANSIBLE_ASYNC_DIR' is not set.")

        finder.scan_exec_script('async_wrapper.ps1')
        actions.append(
            _ManifestAction(
                name='async_wrapper.ps1',
                params={
                    'AsyncDir': async_dir,
                    'AsyncJid': f'j{secrets.randbelow(999999999999)}',
                    'StartupTimeout': C.config.get_config_value("WIN_ASYNC_STARTUP_TIMEOUT", variables=task_vars),
                },
            )
        )

        finder.scan_exec_script('async_watchdog.ps1')
        actions.append(
            _ManifestAction(
                name='async_watchdog.ps1',
                params={
                    'Timeout': async_timeout,
                },
            )
        )

    coverage_output = C.config.get_config_value('COVERAGE_REMOTE_OUTPUT', variables=task_vars)
    if coverage_output and substyle == 'powershell':
        path_filter = C.config.get_config_value('COVERAGE_REMOTE_PATHS', variables=task_vars)

        finder.scan_exec_script('coverage_wrapper.ps1')
        actions.append(
            _ManifestAction(
                name='coverage_wrapper.ps1',
                params={
                    'ModuleName': name_with_ext,
                    'OutputPath': coverage_output,
                    'PathFilter': path_filter,
                },
            )
        )

    actions.append(
        _ManifestAction(
            name='module_wrapper.ps1',
            params=module_params,
        ),
    )

    temp_path: str | None = None
    for temp_key in ['_ansible_tmpdir', '_ansible_remote_tmp']:
        if temp_value := module_args.get(temp_key, None):
            temp_path = temp_value
            break

    exec_manifest = _ExecManifest(
        scripts=finder.scripts,
        actions=actions,
        signed_hashlist=list(finder.signed_hashlist),
    )

    return _get_bootstrap_input(
        exec_manifest,
        min_os_version=finder.os_version,
        min_ps_version=finder.ps_version,
        temp_path=temp_path,
        pwsh_interpreter=pwsh_interpreter,
    )
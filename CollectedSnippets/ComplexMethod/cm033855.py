def _find_module_utils(
        *,
        module_name: str,
        b_module_data: bytes,
        module_path: str,
        module_args: dict[object, object],
        task_vars: dict[str, object],
        templar: Templar,
        module_compression: str,
        async_timeout: int,
        become_plugin: BecomeBase | None,
        environment: dict[str, str],
        remote_is_local: bool = False,
        platform: t.Literal["posix", "windows"] = "posix",
        default_interpreters: dict[str, str] | None = None,
) -> _BuiltModule:
    """
    Given the source of the module, convert it to a Jinja2 template to insert
    module code and return whether it's a new or old style module.
    """
    module_substyle: t.Literal['binary', 'jsonargs', 'non_native_want_json', 'old', 'powershell', 'python']
    module_style: t.Literal['binary', 'new', 'non_native_want_json', 'old']
    module_substyle = module_style = 'old'

    # module_style is something important to calling code (ActionBase).  It
    # determines how arguments are formatted (json vs k=v) and whether
    # a separate arguments file needs to be sent over the wire.
    # module_substyle is extra information that's useful internally.  It tells
    # us what we have to look to substitute in the module files and whether
    # we're using module replacer or ansiballz to format the module itself.
    if _is_binary(b_module_data):
        module_substyle = module_style = 'binary'
    elif REPLACER in b_module_data:
        # Do REPLACER before from ansible.module_utils because we need make sure
        # we substitute "from ansible.module_utils basic" for REPLACER
        module_style = 'new'
        module_substyle = 'python'
        b_module_data = b_module_data.replace(REPLACER, b'from ansible.module_utils.basic import *')
    elif NEW_STYLE_PYTHON_MODULE_RE.search(b_module_data):
        module_style = 'new'
        module_substyle = 'python'
    elif REPLACER_WINDOWS in b_module_data:
        module_style = 'new'
        module_substyle = 'powershell'
        b_module_data = b_module_data.replace(REPLACER_WINDOWS, b'#AnsibleRequires -PowerShell Ansible.ModuleUtils.Legacy')
    elif re.search(b'#Requires -Module', b_module_data, re.IGNORECASE) \
            or re.search(b'#Requires -Version', b_module_data, re.IGNORECASE) \
            or re.search(b'#AnsibleRequires -(OSVersion|PowerShell|CSharpUtil|Wrapper)', b_module_data, re.IGNORECASE):
        module_style = 'new'
        module_substyle = 'powershell'
    elif REPLACER_JSONARGS in b_module_data:
        module_style = 'new'
        module_substyle = 'jsonargs'
    elif b'WANT_JSON' in b_module_data:
        module_substyle = module_style = 'non_native_want_json'

    shebang = None
    # Neither old-style, non_native_want_json nor binary modules should be modified
    # except for the shebang line (Done by modify_module)
    if module_style in ('old', 'non_native_want_json', 'binary'):
        return _BuiltModule(
            b_module_data=b"",  # Marker to indicate the original file should be used without modification.
            module_style=module_style,
            shebang=shebang,
            serialization_profile='legacy',
        )

    output = BytesIO()

    try:
        remote_module_fqn = _get_ansible_module_fqn(module_path)
    except ValueError:
        # Modules in roles currently are not found by the fqn heuristic so we
        # fallback to this.  This means that relative imports inside a module from
        # a role may fail.  Absolute imports should be used for future-proofness.
        # People should start writing collections instead of modules in roles so we
        # may never fix this
        display.debug('ANSIBALLZ: Could not determine module FQN')
        # FIXME: add integration test to validate that builtins and legacy modules with the same name are tracked separately by the caching mechanism
        # FIXME: surrogate FQN should be unique per source path- role-packaged modules with name collisions can still be aliased
        remote_module_fqn = 'ansible.legacy.%s' % module_name

    has_async = False
    has_become = False
    has_environment = False
    command_lookup: _GetCommandArgs | None = None
    process_result: _ProcessResult | None = None

    if module_substyle == 'python':
        date_time = datetime.datetime.now(datetime.timezone.utc)

        if date_time.year < 1980:
            raise AnsibleError(f'Cannot create zipfile due to pre-1980 configured date: {date_time}')

        try:
            compression_method = getattr(zipfile, module_compression)
        except AttributeError:
            display.warning(u'Bad module compression string specified: %s.  Using ZIP_STORED (no compression)' % module_compression)
            compression_method = zipfile.ZIP_STORED

        extension_manager = _builder.ExtensionManager.create(task_vars=task_vars)
        extension_key = '~'.join(extension_manager.extension_names) if extension_manager.extension_names else 'none'
        lookup_path = os.path.join(C.DEFAULT_LOCAL_TMP, 'ansiballz_cache')  # type: ignore[attr-defined]
        cached_module_filename = os.path.join(lookup_path, '-'.join((remote_module_fqn, module_compression, extension_key)))

        os.makedirs(os.path.dirname(cached_module_filename), exist_ok=True)

        cached_module: _CachedModule | None = None

        # Optimization -- don't lock if the module has already been cached
        if os.path.exists(cached_module_filename):
            display.debug('ANSIBALLZ: using cached module: %s' % cached_module_filename)
            cached_module = _CachedModule.load(cached_module_filename)
        else:
            display.debug('ANSIBALLZ: Acquiring lock')
            lock_path = f'{cached_module_filename}.lock'
            with _locking.named_mutex(lock_path):
                display.debug(f'ANSIBALLZ: Lock acquired: {lock_path}')
                # Check that no other process has created this while we were
                # waiting for the lock
                if not os.path.exists(cached_module_filename):
                    display.debug('ANSIBALLZ: Creating module')
                    # Create the module zip data
                    zipoutput = BytesIO()
                    zf = zipfile.ZipFile(zipoutput, mode='w', compression=compression_method)

                    # walk the module imports, looking for module_utils to send- they'll be added to the zipfile
                    module_metadata = recursive_finder(
                        module_name,
                        remote_module_fqn,
                        Origin(path=module_path).tag(b_module_data),
                        zf,
                        date_time,
                        extension_manager,
                    )

                    display.debug('ANSIBALLZ: Writing module into payload')
                    _add_module_to_zip(zf, date_time, remote_module_fqn, b_module_data, module_path, extension_manager)

                    zf.close()
                    zip_data = base64.b64encode(zipoutput.getvalue())

                    # Write the assembled module to a temp file (write to temp
                    # so that no one looking for the file reads a partially
                    # written file)
                    os.makedirs(lookup_path, exist_ok=True)
                    display.debug('ANSIBALLZ: Writing module')
                    cached_module = _CachedModule(zip_data=zip_data, metadata=module_metadata, source_mapping=extension_manager.source_mapping)
                    cached_module.dump(cached_module_filename)
                    display.debug('ANSIBALLZ: Done creating module')

            if not cached_module:
                display.debug('ANSIBALLZ: Reading module after lock')
                # Another process wrote the file while we were waiting for
                # the write lock.  Go ahead and read the data from disk
                # instead of re-creating it.
                try:
                    cached_module = _CachedModule.load(cached_module_filename)
                except OSError as ex:
                    raise AnsibleError('A different worker process failed to create module file. '
                                       'Look at traceback for that process for debugging information.') from ex

        o_interpreter, o_args = _extract_interpreter(b_module_data)
        if o_interpreter is None:
            o_interpreter = u'/usr/bin/python'

        shebang, dummy = _get_shebang(
            o_interpreter,
            task_vars,
            templar,
            o_args,
            remote_is_local=remote_is_local,
            default_interpreters=default_interpreters,
        )

        # FUTURE: the module cache entry should be invalidated if we got this value from a host-dependent source
        rlimit_nofile = C.config.get_config_value('PYTHON_MODULE_RLIMIT_NOFILE', variables=task_vars)

        if not isinstance(rlimit_nofile, int):
            rlimit_nofile = int(templar._engine.template(rlimit_nofile, options=TemplateOptions(value_for_omit=0)))

        if not isinstance(cached_module.metadata, ModuleMetadataV1):
            raise NotImplementedError()

        params = dict(ANSIBLE_MODULE_ARGS=module_args,)
        encoder = get_module_encoder(cached_module.metadata.serialization_profile, Direction.CONTROLLER_TO_MODULE)

        try:
            encoded_params = json.dumps(params, cls=encoder)
        except TypeError as ex:
            raise AnsibleError(f'Failed to serialize arguments for the {module_name!r} module.') from ex

        extension_manager.source_mapping = cached_module.source_mapping

        code = _get_ansiballz_code(shebang)
        args = dict(
            ansible_module=module_name,
            module_fqn=remote_module_fqn,
            profile=cached_module.metadata.serialization_profile,
            date_time=date_time,
            rlimit_nofile=rlimit_nofile,
            params=encoded_params,
            extensions=extension_manager.get_extensions(),
            zip_data=to_text(cached_module.zip_data),
        )

        args_string = '\n'.join(f'{key}={value!r},' for key, value in args.items())

        wrapper = f"""{code}


if __name__ == "__main__":
    _ansiballz_main(
{args_string}
)
"""

        output.write(to_bytes(wrapper))

        module_metadata = cached_module.metadata
        b_module_data = output.getvalue()

    elif module_substyle == 'powershell':
        module_metadata = ModuleMetadataV1(serialization_profile='legacy')  # DTFIX-FUTURE: support serialization profiles for PowerShell modules

        wrapper_environment = {}
        wrapper_async_timeout = 0
        wrapper_become = None

        if platform == "windows":
            # Async, become, and environment support in the wrapper is Windows only.
            wrapper_environment = environment
            wrapper_async_timeout = async_timeout
            wrapper_become = become_plugin
            has_async = True
            has_become = True
            has_environment = True

        module_interpreter, dummy = _extract_interpreter(b_module_data)
        if not module_interpreter:
            module_interpreter = 'powershell'

        shebang, dummy = _get_shebang(
            module_interpreter,
            task_vars,
            templar,
            default_interpreters=default_interpreters,
        )

        # We pass the interpreter to the exec wrapper in case the connection
        # plugin (psrp) is unable to control what interpreter to use.
        pwsh_interpreter = shebang[2:]  # Drop the #!

        # create the common exec wrapper payload and set that as the module_data
        # bytes
        b_module_data = ps_manifest._create_powershell_wrapper(
            name=remote_module_fqn,
            module_data=b_module_data,
            module_path=module_path,
            module_args=module_args,
            environment=wrapper_environment,
            async_timeout=wrapper_async_timeout,
            become_plugin=wrapper_become,
            substyle=module_substyle,
            task_vars=task_vars,
            profile=module_metadata.serialization_profile,
            pwsh_interpreter=pwsh_interpreter,
        )

        def get_module_command_args(
            module_path: str | None,
        ) -> tuple[list[str], bytes | None] | None:
            bootstrap_wrapper = ps_manifest._get_powershell_script("bootstrap_wrapper.ps1").decode('utf-8')

            module_data = None
            bootstrap_args = []
            disable_input = False
            if not module_path:
                # We are pipelining
                module_data = b_module_data
            else:
                # Running powershell without any input might hang the process
                # if the parent spawns powershell with a redirected stdin but
                # never closes it. By explicitly disabling the input,
                # powershell never attempts to wait for stdin to close.
                disable_input = True
                bootstrap_args = [module_path]

            interpreter_args = _ps_script.get_pwsh_encoded_cmdline(
                script=bootstrap_wrapper,
                args=bootstrap_args,
                pwsh_path=pwsh_interpreter,
                disable_input=disable_input,
                override_execution_policy=platform == "windows",
            )

            return interpreter_args, module_data

        def parse_clixml_stderr(rc: int, stdout: bytes, stderr: bytes) -> tuple[int, bytes, bytes]:
            return (rc, stdout, _clixml.replace_stderr_clixml(stderr))

        command_lookup = get_module_command_args
        process_result = parse_clixml_stderr

    elif module_substyle == 'jsonargs':
        encoder = get_module_encoder('legacy', Direction.CONTROLLER_TO_MODULE)
        module_args_json = to_bytes(json.dumps(module_args, cls=encoder))

        # these strings could be included in a third-party module but
        # officially they were included in the 'basic' snippet for new-style
        # python modules (which has been replaced with something else in
        # ansiballz) If we remove them from jsonargs-style module replacer
        # then we can remove them everywhere.
        python_repred_args = to_bytes(repr(module_args_json))
        b_module_data = b_module_data.replace(REPLACER_VERSION, to_bytes(repr(__version__)))
        b_module_data = b_module_data.replace(REPLACER_COMPLEX, python_repred_args)
        b_module_data = b_module_data.replace(
            REPLACER_SELINUX,
            to_bytes(','.join(C.DEFAULT_SELINUX_SPECIAL_FS)))  # type: ignore[attr-defined]

        # The main event -- substitute the JSON args string into the module
        b_module_data = b_module_data.replace(REPLACER_JSONARGS, module_args_json)

        syslog_facility = task_vars.get(
            'ansible_syslog_facility',
            C.DEFAULT_SYSLOG_FACILITY)  # type: ignore[attr-defined]
        facility = b'syslog.' + to_bytes(syslog_facility, errors='surrogate_or_strict')
        b_module_data = b_module_data.replace(b'syslog.LOG_USER', facility)

        module_metadata = ModuleMetadataV1(serialization_profile='legacy')
    else:
        module_metadata = ModuleMetadataV1(serialization_profile='legacy')

    if not isinstance(module_metadata, ModuleMetadataV1):
        raise NotImplementedError(type(module_metadata))

    return _BuiltModule(
        b_module_data=b_module_data,
        module_style=module_style,
        shebang=shebang,
        serialization_profile=module_metadata.serialization_profile,
        has_async=has_async,
        has_become=has_become,
        has_environment=has_environment,
        command_lookup=command_lookup,
        process_result=process_result,
    )
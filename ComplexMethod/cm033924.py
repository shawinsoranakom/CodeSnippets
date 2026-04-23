def _execute_module(
        self,
        module_name: str | None = None,
        module_args: dict[str, object] | None = None,
        tmp: str | None = None,
        task_vars: dict[str, object] | None = None,
        persist_files: bool = False,
        delete_remote_tmp: bool | None = None,
        wrap_async: bool = False,
        ignore_unknown_opts: bool = False,
    ) -> dict[str, object]:
        """
        Transfer and run a module along with its arguments.
        """
        if tmp is not None:
            display.warning('_execute_module no longer honors the tmp parameter. Action plugins'
                            ' should set self._connection._shell.tmpdir to share the tmpdir')
        del tmp  # No longer used
        if delete_remote_tmp is not None:
            display.warning('_execute_module no longer honors the delete_remote_tmp parameter.'
                            ' Action plugins should check self._connection._shell.tmpdir to'
                            ' see if a tmpdir existed before they were called to determine'
                            ' if they are responsible for removing it.')
        del delete_remote_tmp  # No longer used

        tmpdir = self._connection._shell.tmpdir

        # We set the module_style to new here so the remote_tmp is created
        # before the module args are built if remote_tmp is needed (async).
        # If the module_style turns out to not be new and we didn't create the
        # remote tmp here, it will still be created. This must be done before
        # calling self._update_module_args() so the module wrapper has the
        # correct remote_tmp value set.
        # FUTURE: Async shouldn't be part of a connection's capabilities but
        # rather part of the module's exec/style caps. The current setup is
        # hard to achieve this as we need to build the module_args before we
        # can build the module so we keep this here for now.
        if not self._is_pipelining_enabled("new", wrap_async) and tmpdir is None:
            self._make_tmp_path()
            tmpdir = self._connection._shell.tmpdir

        if task_vars is None:
            task_vars = dict()

        # if a module name was not specified for this execution, use the action from the task
        if module_name is None:
            module_name = self._task.action
        if module_args is None:
            module_args = self._task.args

        self._update_module_args(module_name, module_args, task_vars, ignore_unknown_opts=ignore_unknown_opts)

        remove_async_dir = None
        if wrap_async or self._task.async_val:
            async_dir = self.get_shell_option('async_dir', default="~/.ansible_async")
            remove_async_dir = len(self._task.environment)
            self._task.environment.append({"ANSIBLE_ASYNC_DIR": async_dir})

        # FUTURE: refactor this along with module build process to better encapsulate "smart wrapper" functionality
        module_bits, module_path = self._configure_module(module_name=module_name, module_args=module_args, task_vars=task_vars)
        (module_style, module_shebang, module_data) = (module_bits.module_style, module_bits.shebang, module_bits.b_module_data)
        display.vvv("Using module file %s" % module_path)
        if not module_shebang and module_style != 'binary':
            raise AnsibleError("module (%s) is missing interpreter line" % module_name)

        # If the module payload has async builtin, e.g. pwsh exec_wrapper, then
        # we can bypass the async_wrapper.py and pipelining checks done for
        # async as it's treated like a normal module.
        wrap_async = wrap_async and not module_bits.has_async

        self._used_interpreter = module_shebang

        # FUTURE: Instead of module_style we should add "capabilities" to the
        # module_bits dataclass that indicate things like argument format.
        # This will reduce the cognitive overload of trying to remember all the
        # different styles and what they mean.
        args_file_path = None
        remote_module_path = None
        remote_files = []
        if not self._is_pipelining_enabled(module_style) or wrap_async:
            if tmpdir is None:
                self._make_tmp_path()
                tmpdir = self._connection._shell.tmpdir

            remote_files.append(tmpdir)

            if module_style != 'new':
                # binary, old, and non_native_want_json module styles use an
                # args file to store the module arguments.
                args_file_path = self._connection._shell.join_path(tmpdir, 'args')
                remote_files.append(args_file_path)

            remote_module_filename = self._connection._shell.get_remote_filename(module_path)
            remote_module_path = self._connection._shell.join_path(tmpdir, 'AnsiballZ_%s' % remote_module_filename)
            remote_files.append(remote_module_path)

            display.debug("transferring module to remote %s" % remote_module_path)
            if module_data:
                # modify_module edited the data in some way, we cannot transfer
                # from the existing path.
                self._transfer_data(remote_module_path, module_data)
            else:
                self._transfer_file(module_path, remote_module_path)

            if args_file_path:
                if module_style == 'old':
                    # we need to dump the module args to a k=v string in a file on
                    # the remote system, which can be read and parsed by the module
                    args_data = ""
                    for k, v in module_args.items():
                        args_data += '%s=%s ' % (k, shlex.quote(str(v)))
                    self._transfer_data(args_file_path, args_data)
                else:
                    profile_encoder = get_module_encoder(module_bits.serialization_profile, Direction.CONTROLLER_TO_MODULE)
                    self._transfer_data(args_file_path, json.dumps(module_args, cls=profile_encoder))

            display.debug("done transferring module to remote")

        environment_string = ''
        if not module_bits.has_environment:
            environment_string = self._compute_environment_string()

        # remove the ANSIBLE_ASYNC_DIR env entry if we added a temporary one for
        # the async_wrapper task.
        if remove_async_dir is not None:
            del self._task.environment[remove_async_dir]

        module_in_data: bytes | None = None
        module_cmd = ''
        module_cmd_args: list[str] = []

        # FUTURE: If we can deprecated and remove shell.build_module_command()
        # we can move all this logic into the get_command_args for all module
        # types rather than it being opt in per exec style.
        if cmd_args := module_bits.get_command_args(remote_module_path):
            module_cmd_args, module_in_data = cmd_args

        else:
            if remote_module_path:
                module_cmd_args = [remote_module_path]
            else:
                module_in_data = module_data

            # We still skip build_module_command if using async as that always
            # built its own command. The async_wrapper expects the full command
            # to run so we need to add the shebang and args path (if set).
            if wrap_async:
                if module_shebang:
                    module_interpreter = module_shebang.replace('#!', '').strip()
                    module_cmd_args.insert(0, module_interpreter)

                if args_file_path:
                    module_cmd_args.append(args_file_path)

            else:
                module_cmd = self._connection._shell.build_module_command(
                    environment_string,
                    module_shebang,
                    " ".join(module_cmd_args),
                    arg_path=args_file_path,
                ).strip()

        if wrap_async:
            # configure, upload, and chmod the async_wrapper module
            (async_module_bits, async_module_path) = self._configure_module(module_name='ansible.legacy.async_wrapper', module_args=dict(), task_vars=task_vars)
            (async_shebang, async_module_data) = (async_module_bits.shebang, async_module_bits.b_module_data)
            async_module_remote_filename = self._connection._shell.get_remote_filename(async_module_path)
            remote_async_module_path = self._connection._shell.join_path(tmpdir, async_module_remote_filename)
            self._transfer_data(remote_async_module_path, async_module_data)
            remote_files.append(remote_async_module_path)

            async_limit = str(self._task.async_val)
            async_jid = f'j{secrets.randbelow(999999999999)}'

            # call the interpreter for async_wrapper directly
            # this permits use of a script for an interpreter on non-Linux platforms
            interpreter = async_shebang.replace('#!', '').strip()

            preserve_tmp = str(not self._should_remove_tmp_path(tmpdir)).lower()
            async_cmd = [interpreter, remote_async_module_path, async_jid, async_limit, preserve_tmp, remote_module_path]
            async_cmd.extend(module_cmd_args)

            module_cmd_args = async_cmd

        if not module_cmd:
            module_cmd = self._connection._shell.join(module_cmd_args)
            if environment_string:
                module_cmd = f"{environment_string} {module_cmd}"

        # Fix permissions of the tmpdir path and tmpdir files. This should be called after all
        # files have been transferred.
        if remote_files:
            # remove none/empty
            remote_files = [x for x in remote_files if x]
            self._fixup_perms2(remote_files, self._get_remote_user())

        # actually execute
        res = self._low_level_execute_command(
            module_cmd,
            sudoable=not module_bits.has_become,
            in_data=module_in_data,
            process_result=module_bits.process_result,
        )

        # parse the main result
        utr = self._parse_returned_data(res, module_bits.serialization_profile)

        # NOTE: INTERNAL KEYS ONLY ACCESSIBLE HERE
        # get internal info before cleaning
        if utr.suppress_tmpdir_delete:
            self._cleanup_remote_tmp = False

        # remove internal keys
        utr.remove_internal_keys()

        if wrap_async:
            # async_wrapper will clean up its tmpdir on its own so we want the controller side to
            # forget about it now
            self._connection._shell.tmpdir = None

            # RPFIX-9: FUTURE: for backward compat (pre-RP), figure out if still makes sense
            utr.changed = True

        # propagate interpreter discovery results back to the controller
        if self._discovered_interpreter_key:
            utr.set_fact(self._discovered_interpreter_key, self._discovered_interpreter)

        display.debug("done with _execute_module (%s, %s)" % (module_name, module_args))
        return utr.as_result_dict(for_round_trip=True)
def run(self, tmp: str | None = None, task_vars: dict[str, _t.Any] | None = None) -> dict[str, _t.Any]:
        """ handler for file transfer operations """
        if task_vars is None:
            task_vars = dict()

        validation_result, new_module_args = self.validate_argument_spec(
            argument_spec={
                '_raw_params': {},
                'cmd': {'type': 'str'},
                'creates': {'type': 'str'},
                'removes': {'type': 'str'},
                'chdir': {'type': 'str'},
                'executable': {'type': 'str'},
            },
            required_one_of=[['_raw_params', 'cmd']],
            mutually_exclusive=[['_raw_params', 'cmd']],
        )

        super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        try:
            creates = new_module_args['creates']
            if creates:
                # do not run the command if the line contains creates=filename
                # and the filename already exists. This allows idempotence
                # of command executions.
                if self._remote_file_exists(creates):
                    raise AnsibleActionSkip("%s exists, matching creates option" % creates)

            removes = new_module_args['removes']
            if removes:
                # do not run the command if the line contains removes=filename
                # and the filename does not exist. This allows idempotence
                # of command executions.
                if not self._remote_file_exists(removes):
                    raise AnsibleActionSkip("%s does not exist, matching removes option" % removes)

            # The chdir must be absolute, because a relative path would rely on
            # remote node behaviour & user config.
            chdir = new_module_args['chdir']
            if chdir:
                # Powershell is the only Windows-path aware shell
                if getattr(self._connection._shell, "_IS_WINDOWS", False) and \
                        not self.windows_absolute_path_detection.match(chdir):
                    raise AnsibleActionFail('chdir %s must be an absolute path for a Windows remote node' % chdir)
                # Every other shell is unix-path-aware.
                if not getattr(self._connection._shell, "_IS_WINDOWS", False) and not chdir.startswith('/'):
                    raise AnsibleActionFail('chdir %s must be an absolute path for a Unix-aware remote node' % chdir)

            # Split out the script as the first item in raw_params using
            # shlex.split() in order to support paths and files with spaces in the name.
            # Any arguments passed to the script will be added back later.
            raw_params = new_module_args['_raw_params'] or new_module_args['cmd']
            parts = [to_text(s, errors='surrogate_or_strict') for s in shlex.split(raw_params.strip())]
            source = parts[0]

            # Support executable paths and files with spaces in the name.
            executable = new_module_args['executable']
            if executable:
                executable = to_native(new_module_args['executable'], errors='surrogate_or_strict')
            try:
                source = self._loader.get_real_file(self._find_needle('files', source))
            except AnsibleError as e:
                raise AnsibleActionFail(to_native(e))

            if self._task.check_mode:
                # check mode is supported if 'creates' or 'removes' are provided
                # the task has already been skipped if a change would not occur
                if new_module_args['creates'] or new_module_args['removes']:
                    return dict(changed=True)
                # If the script doesn't return changed in the result, it defaults to True,
                # but since the script may override 'changed', just skip instead of guessing.
                else:
                    raise AnsibleActionSkip('Check mode is not supported for this task.', result=dict(changed=False))

            # transfer the file to a remote tmp location
            tmp_src = self._connection._shell.join_path(self._connection._shell.tmpdir,
                                                        os.path.basename(source))

            # Convert raw_params to text for the purpose of replacing the script since
            # parts and tmp_src are both unicode strings and raw_params will be different
            # depending on Python version.
            #
            # Once everything is encoded consistently, replace the script path on the remote
            # system with the remainder of the raw_params. This preserves quoting in parameters
            # that would have been removed by shlex.split().
            target_command = to_text(raw_params).strip().replace(parts[0], tmp_src)

            self._transfer_file(source, tmp_src)

            # set file permissions, more permissive when the copy is done as a different user
            self._fixup_perms2((self._connection._shell.tmpdir, tmp_src), execute=True)

            # add preparation steps to one ssh roundtrip executing the script
            env_dict: dict[str, _t.Any] = {}
            env_string = self._compute_environment_string(env_dict)

            if executable:
                script_cmd = ' '.join([env_string, executable, target_command])
            else:
                script_cmd = ' '.join([env_string, target_command])

            exec_data = None
            # PowerShell runs the script in a special wrapper to enable things
            # like become and environment args
            if getattr(self._connection._shell, "_IS_WINDOWS", False):
                # FUTURE: use a more public method to get the exec payload
                exec_data = ps_manifest._create_powershell_wrapper(
                    name=f"ansible.builtin.script.{pathlib.Path(source).stem}",
                    module_data=to_bytes(f"& {script_cmd}; exit $LASTEXITCODE"),
                    module_path=source,
                    module_args={},
                    environment=env_dict,
                    async_timeout=self._task.async_val,
                    become_plugin=self._connection.become,
                    substyle="script",
                    task_vars=task_vars,
                    profile='legacy',  # the profile doesn't really matter since the module args dict is empty
                )
                bootstrap_wrapper = ps_manifest._get_powershell_script("bootstrap_wrapper.ps1").decode('utf-8')
                pwsh_args = _ps_script.get_pwsh_encoded_cmdline(bootstrap_wrapper, override_execution_policy=True)
                script_cmd = self._connection._shell.join(pwsh_args)

            # now we execute script, always assume changed.
            result: dict[str, object] = dict(self._low_level_execute_command(cmd=script_cmd, in_data=exec_data, sudoable=True, chdir=chdir), changed=True)

            if 'rc' in result and result['rc'] != 0:
                result.update(msg='non-zero return code', failed=True)

            return result
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)
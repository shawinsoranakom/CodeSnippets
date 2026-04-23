def setup_virtualenv(module, env, chdir, out, err):
    if module.check_mode:
        module.exit_json(changed=True)

    cmd = shlex.split(module.params['virtualenv_command'])

    # Find the binary for the command in the PATH
    # and switch the command for the explicit path.
    if os.path.basename(cmd[0]) == cmd[0]:
        cmd[0] = module.get_bin_path(cmd[0], True)

    # Add the system-site-packages option if that
    # is enabled, otherwise explicitly set the option
    # to not use system-site-packages if that is an
    # option provided by the command's help function.
    if module.params['virtualenv_site_packages']:
        cmd.append('--system-site-packages')
    else:
        cmd_opts = _get_cmd_options(module, cmd[0])
        if '--no-site-packages' in cmd_opts:
            cmd.append('--no-site-packages')

    virtualenv_python = module.params['virtualenv_python']
    # -p is a virtualenv option, not compatible with pyenv or venv
    # this conditional validates if the command being used is not any of them
    if not _is_venv_command(module.params['virtualenv_command']):
        if virtualenv_python:
            cmd.append('-p%s' % virtualenv_python)
        else:
            # This code mimics the upstream behaviour of using the python
            # which invoked virtualenv to determine which python is used
            # inside of the virtualenv (when none are specified).
            cmd.append('-p%s' % sys.executable)

    # if venv or pyvenv are used and virtualenv_python is defined, then
    # virtualenv_python is ignored, this has to be acknowledged
    elif module.params['virtualenv_python']:
        module.fail_json(
            msg='virtualenv_python should not be used when'
                ' using the venv module or pyvenv as virtualenv_command'
        )

    cmd.append(env)
    rc, out_venv, err_venv = module.run_command(cmd, cwd=chdir)
    out += out_venv
    err += err_venv
    if rc != 0:
        _fail(module, cmd, out, err)
    return out, err, cmd
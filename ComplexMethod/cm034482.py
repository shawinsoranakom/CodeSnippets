def _get_pip(module, env=None, executable=None):
    candidate_pip_basenames = ('pip3',)
    pip = None
    if executable is not None:
        if os.path.isabs(executable):
            pip = executable
        else:
            # If you define your own executable that executable should be the only candidate.
            # As noted in the docs, executable doesn't work with virtualenvs.
            candidate_pip_basenames = (executable,)
    elif executable is None and env is None and _have_pip_module():
        # If no executable or virtualenv were specified, use the pip module for the current Python interpreter if available.
        pip = [sys.executable, '-m', 'pip']

    if pip is None:
        if env is None:
            opt_dirs = []
            for basename in candidate_pip_basenames:
                pip = module.get_bin_path(basename, False, opt_dirs)
                if pip is not None:
                    break
            else:
                # For-else: Means that we did not break out of the loop
                # (therefore, that pip was not found)
                module.fail_json(msg='Unable to find any of %s to use.  pip'
                                     ' needs to be installed.' % ', '.join(candidate_pip_basenames))
        else:
            # If we're using a virtualenv we must use the pip from the
            # virtualenv
            venv_dir = os.path.join(env, 'bin')
            candidate_pip_basenames = (candidate_pip_basenames[0], 'pip')
            for basename in candidate_pip_basenames:
                candidate = os.path.join(venv_dir, basename)
                if os.path.exists(candidate) and is_executable(candidate):
                    pip = candidate
                    break
            else:
                # For-else: Means that we did not break out of the loop
                # (therefore, that pip was not found)
                module.fail_json(msg='Unable to find pip in the virtualenv, %s, ' % env +
                                     'under any of these names: %s. ' % (', '.join(candidate_pip_basenames)) +
                                     'Make sure pip is present in the virtualenv.')

    if not isinstance(pip, list):
        pip = [pip]

    return pip
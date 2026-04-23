def main():
    state_map = dict(
        present=['install'],
        absent=['uninstall', '-y'],
        latest=['install', '-U'],
        forcereinstall=['install', '-U', '--force-reinstall'],
    )

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=list(state_map.keys())),
            name=dict(type='list', elements='str'),
            version=dict(type='str'),
            requirements=dict(type='str'),
            virtualenv=dict(type='path'),
            virtualenv_site_packages=dict(type='bool', default=False),
            virtualenv_command=dict(type='path', default='virtualenv'),
            virtualenv_python=dict(type='str'),
            extra_args=dict(type='str'),
            editable=dict(type='bool', default=False),
            chdir=dict(type='path'),
            executable=dict(type='path'),
            umask=dict(type='str'),
            break_system_packages=dict(type='bool', default=False),
        ),
        required_one_of=[['name', 'requirements']],
        mutually_exclusive=[
            ['name', 'requirements'],
            ['executable', 'virtualenv'],
            ['editable', 'requirements'],
        ],
        supports_check_mode=True,
    )

    if not HAS_SETUPTOOLS and not HAS_PACKAGING:
        module.fail_json(msg=missing_required_lib("packaging"),
                         exception=PACKAGING_IMP_ERR)

    state = module.params['state']
    name = module.params['name']
    version = module.params['version']
    requirements = module.params['requirements']
    extra_args = module.params['extra_args']
    chdir = module.params['chdir']
    umask = module.params['umask']
    env = module.params['virtualenv']
    editable = module.params['editable']

    venv_created = False
    if env and chdir:
        env = os.path.join(chdir, env)

    if umask and not isinstance(umask, int):
        try:
            umask = int(umask, 8)
        except Exception:
            module.fail_json(msg="umask must be an octal integer",
                             details=to_native(sys.exc_info()[1]))

    old_umask = None
    if umask is not None:
        old_umask = os.umask(umask)
    try:
        if state == 'latest' and version is not None:
            module.fail_json(msg='version is incompatible with state=latest')

        if chdir is None:
            # this is done to avoid permissions issues with privilege escalation and virtualenvs
            chdir = tempfile.gettempdir()

        err = ''
        out = ''
        venv_cmd = ''

        if env:
            if not os.path.exists(os.path.join(env, 'bin', 'activate')):
                venv_created = True
                out, err, venv_cmd = setup_virtualenv(module, env, chdir, out, err)
            py_bin = os.path.join(env, 'bin', 'python')
        else:
            py_bin = module.params['executable'] or sys.executable

        pip = _get_pip(module, env, module.params['executable'])

        cmd = pip + state_map[state]

        # If there's a virtualenv we want things we install to be able to use other
        # installations that exist as binaries within this virtualenv. Example: we
        # install cython and then gevent -- gevent needs to use the cython binary,
        # not just a python package that will be found by calling the right python.
        # So if there's a virtualenv, we add that bin/ to the beginning of the PATH
        # in run_command by setting path_prefix here.
        path_prefix = None
        if env:
            path_prefix = os.path.join(env, 'bin')

        # Automatically apply -e option to extra_args when source is a VCS url. VCS
        # includes those beginning with svn+, git+, hg+ or bzr+
        has_vcs = False
        if name:
            for pkg in name:
                if pkg and _is_vcs_url(pkg):
                    has_vcs = True
                    break

            # convert raw input package names to Package instances
            packages = [Package(pkg) for pkg in _recover_package_name(name)]
            # check invalid combination of arguments
            if version is not None:
                if len(packages) > 1:
                    module.fail_json(
                        msg="'version' argument is ambiguous when installing multiple package distributions. "
                            "Please specify version restrictions next to each package in 'name' argument."
                    )
                if packages[0].has_version_specifier:
                    module.fail_json(
                        msg="The 'version' argument conflicts with any version specifier provided along with a package name. "
                            "Please keep the version specifier, but remove the 'version' argument."
                    )
                # if the version specifier is provided by version, append that into the package
                packages[0] = Package(to_native(packages[0]), version)

        if extra_args:
            cmd.extend(shlex.split(extra_args))

        if module.params['break_system_packages']:
            # Using an env var instead of the `--break-system-packages` option, to avoid failing under pip 23.0.0 and earlier.
            # See: https://github.com/pypa/pip/pull/11780
            os.environ['PIP_BREAK_SYSTEM_PACKAGES'] = '1'

        if name:
            for p in packages:
                if editable:
                    cmd.append('-e')
                cmd.append(to_native(p))
        elif requirements:
            cmd.extend(['-r', requirements])
        elif venv_created and not name and not requirements:
            # ONLY creating an empty venv
            module.exit_json(changed=venv_created, cmd=venv_cmd, name=name, version=version,
                             state=state, requirements=requirements, virtualenv=env,
                             stdout=out, stderr=err)
        else:
            module.warn("No valid name or requirements file found.")
            module.exit_json(changed=False)

        if module.check_mode:
            if extra_args or requirements or state == 'latest' or not name:
                module.exit_json(changed=True)

            pkg_cmd, out_pip, err_pip = _get_packages(module, pip, chdir)

            out += out_pip
            err += err_pip

            changed = False
            if name:
                pkg_list = [p for p in out.split('\n') if not p.startswith('You are using') and not p.startswith('You should consider') and p]

                if pkg_cmd.endswith(' freeze') and ('pip' in name or 'setuptools' in name):
                    # Older versions of pip (pre-1.3) do not have pip list.
                    # pip freeze does not list setuptools or pip in its output
                    # So we need to get those via a specialcase
                    for pkg in ('setuptools', 'pip'):
                        if pkg in name:
                            formatted_dep = _get_package_info(module, pkg, py_bin)
                            if formatted_dep is not None:
                                pkg_list.append(formatted_dep)
                                out += '%s\n' % formatted_dep

                normalized_package_list = _resolve_package_names(module, packages, pip, py_bin)

                for package in normalized_package_list:
                    is_present = _is_present(module, package, pkg_list, pkg_cmd)
                    if (state == 'present' and not is_present) or (state == 'absent' and is_present):
                        changed = True
                        break
            module.exit_json(changed=changed, cmd=pkg_cmd, stdout=out, stderr=err)

        out_freeze_before = None
        if requirements or has_vcs:
            dummy, out_freeze_before, dummy = _get_packages(module, pip, chdir)

        rc, out_pip, err_pip = module.run_command(cmd, path_prefix=path_prefix, cwd=chdir)
        out += out_pip
        err += err_pip
        if rc == 1 and state == 'absent' and \
           ('not installed' in out_pip or 'not installed' in err_pip):
            pass  # rc is 1 when attempting to uninstall non-installed package
        elif rc != 0:
            _fail(module, cmd, out, err)

        if state == 'absent':
            changed = 'Successfully uninstalled' in out_pip
        else:
            if out_freeze_before is None:
                changed = 'Successfully installed' in out_pip
            else:
                dummy, out_freeze_after, dummy = _get_packages(module, pip, chdir)
                changed = out_freeze_before != out_freeze_after

        changed = changed or venv_created

        module.exit_json(changed=changed, cmd=cmd, name=name, version=version,
                         state=state, requirements=requirements, virtualenv=env,
                         stdout=out, stderr=err)
    finally:
        if old_umask is not None:
            os.umask(old_umask)
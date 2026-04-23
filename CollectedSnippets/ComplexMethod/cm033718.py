def create_sanity_virtualenv(
    args: SanityConfig,
    python: PythonConfig,
    name: str,
    coverage: bool = False,
    minimize: bool = False,
) -> t.Optional[VirtualPythonConfig]:
    """Return an existing sanity virtual environment matching the requested parameters or create a new one."""
    commands = collect_requirements(  # create_sanity_virtualenv()
        python=python,
        controller=True,
        command=None,
        ansible=False,
        coverage=coverage,
        minimize=minimize,
        sanity=name,
    )

    if commands:
        label = f'sanity.{name}'
    else:
        label = 'sanity'  # use a single virtualenv name for tests which have no requirements

    # The path to the virtual environment must be kept short to avoid the 127 character shebang length limit on Linux.
    # If the limit is exceeded, generated entry point scripts from pip installed packages will fail with syntax errors.
    virtualenv_install = json.dumps([command.serialize() for command in commands], indent=4)
    virtualenv_hash = hash_pip_commands(commands)
    virtualenv_cache = os.path.join(os.path.expanduser('~/.ansible/test/venv'))
    virtualenv_path = os.path.join(virtualenv_cache, label, f'{python.version}', virtualenv_hash)
    virtualenv_marker = os.path.join(virtualenv_path, 'marker.txt')

    meta_install = os.path.join(virtualenv_path, 'meta.install.json')
    meta_yaml = os.path.join(virtualenv_path, 'meta.yaml.json')

    virtualenv_python = VirtualPythonConfig(
        version=python.version,
        path=os.path.join(virtualenv_path, 'bin', 'python'),
    )

    if not os.path.exists(virtualenv_marker):
        # a virtualenv without a marker is assumed to have been partially created
        remove_tree(virtualenv_path)

        if not create_virtual_environment(args, python, virtualenv_path):
            return None

        run_pip(args, virtualenv_python, commands, None)  # create_sanity_virtualenv()

        if not args.explain:
            write_text_file(meta_install, virtualenv_install)

        # false positive: pylint: disable=no-member
        if any(isinstance(command, PipInstall) and command.has_package('pyyaml') for command in commands):
            virtualenv_yaml = yamlcheck(virtualenv_python, args.explain)
        else:
            virtualenv_yaml = None

        if not args.explain:
            write_json_file(meta_yaml, virtualenv_yaml)

        created_venvs.append(f'{label}-{python.version}')

    if not args.explain:
        # touch the marker to keep track of when the virtualenv was last used
        pathlib.Path(virtualenv_marker).touch()

    return virtualenv_python
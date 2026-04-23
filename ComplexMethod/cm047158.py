def load_addons_commands(command=None):
    """
    Search the addons path for modules with a ``cli/{command}.py`` file.
    In case no command is provided, discover and load all the commands.
    """
    if command is None:
        command = '*'
    elif not Command.is_valid_name(command):
        return

    mapping = {}
    initialize_sys_path()
    for path in odoo.addons.__path__:
        for fullpath in Path(path).glob(f'*/cli/{command}.py'):
            if (found_command := fullpath.stem) and Command.is_valid_name(found_command):
                # loading as odoo.cli and not odoo.addons.{module}.cli
                # so it doesn't load odoo.addons.{module}.__init__
                mapping[f'odoo.cli.{found_command}'] = fullpath 

    for fq_name, fullpath in mapping.items():
        with contextlib.suppress(ImportError):
            load_script(fullpath, fq_name)
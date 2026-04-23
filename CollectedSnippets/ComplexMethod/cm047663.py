def get_translated_module(arg: str | int | typing.Any) -> str:  # frame not represented as hint
    """Get the addons name.

    :param arg: can be any of the following:
                str ("name_of_module") returns itself;
                str (__name__) use to resolve module name;
                int is number of frames to go back to the caller;
                frame of the caller function
    """
    if isinstance(arg, str):
        if arg.startswith('odoo.addons.'):
            # get the name of the module
            return arg.split('.')[2]
        if '.' in arg or not arg:
            # module name is not in odoo.addons.
            return 'base'
        else:
            return arg
    else:
        if isinstance(arg, int):
            frame = inspect.currentframe()
            while arg > 0:
                arg -= 1
                frame = frame.f_back
        else:
            frame = arg
        if not frame:
            return 'base'
        if (module_name := frame.f_globals.get("__name__")) and module_name.startswith('odoo.addons.'):
            # just a quick lookup because `get_resource_from_path is slow compared to this`
            return module_name.split('.')[2]
        path = inspect.getfile(frame)
        from odoo.modules import get_resource_from_path  # noqa: PLC0415
        path_info = get_resource_from_path(path)
        return path_info[0] if path_info else 'base'
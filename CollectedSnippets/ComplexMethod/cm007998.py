def load_plugins(plugin_spec: PluginSpec):
    name, suffix = plugin_spec.module_name, plugin_spec.suffix
    regular_classes = {}
    if os.environ.get('YTDLP_NO_PLUGINS') or not plugin_dirs.value:
        return regular_classes

    for finder, module_name, _ in iter_modules(name):
        if any(x.startswith('_') for x in module_name.split('.')):
            continue
        try:
            spec = finder.find_spec(module_name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception:
            write_string(
                f'Error while importing module {module_name!r}\n{traceback.format_exc(limit=-1)}',
            )
            continue
        regular_classes.update(get_regular_classes(module, module_name, suffix))

    # Compat: old plugin system using __init__.py
    # Note: plugins imported this way do not show up in directories()
    # nor are considered part of the yt_dlp_plugins namespace package
    if 'default' in plugin_dirs.value:
        with contextlib.suppress(FileNotFoundError):
            spec = importlib.util.spec_from_file_location(
                name,
                Path(get_executable_path(), COMPAT_PACKAGE_NAME, name, '__init__.py'),
            )
            plugins = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = plugins
            spec.loader.exec_module(plugins)
            regular_classes.update(get_regular_classes(plugins, spec.name, suffix))

    # Add the classes into the global plugin lookup for that type
    plugin_spec.plugin_destination.value = regular_classes
    # We want to prepend to the main lookup for that type
    plugin_spec.destination.value = merge_dicts(regular_classes, plugin_spec.destination.value)

    return regular_classes
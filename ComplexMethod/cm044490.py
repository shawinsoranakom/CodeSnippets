def generate_configs(force: bool = False) -> None:
    """ Generate config files if they don't exist.

    This script is run prior to anything being set up, so don't use logging
    Generates the default config files for plugins in the faceswap config folder

    Logic:
        - Scan the plugins path for files named <parent_folder>_config.py>
        - Import the discovered module and look for instances of FaceswapConfig
        - If exists initialize the class

    Parameters
    ----------
    force : bool
        Force the loading of all plugin configs even if their .ini files pre-exist
    """
    configs_path = os.path.join(PROJECT_ROOT, "config")
    plugins_path = os.path.join(PROJECT_ROOT, "plugins")
    for dirpath, _, filenames in os.walk(plugins_path):
        relative_path = dirpath.replace(PROJECT_ROOT, "")[1:]
        if len(full_path_split(relative_path)) > 2:  # don't dig further than 1 folder deep
            continue
        plugin_group = os.path.basename(dirpath)
        filename = f"{plugin_group}_config.py"
        if filename not in filenames:
            continue

        if plugin_group in _CONFIGS:
            continue

        config_file = os.path.join(configs_path, f"{plugin_group}.ini")
        if not os.path.exists(config_file) or force:
            mod_name = os.path.splitext(filename)[0]
            mod_path = os.path.join(dirpath.replace(PROJECT_ROOT, ""),
                                    mod_name)[1:].replace(os.sep, ".")
            mod = import_module(mod_path)
            for obj in vars(mod).values():
                if (inspect.isclass(obj)
                        and issubclass(obj, FaceswapConfig)
                        and obj != FaceswapConfig):
                    obj()
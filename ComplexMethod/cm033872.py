def __init__(
        self,
        class_name: str,
        package: str,
        config: str | list[str],
        subdir: str,
        aliases: dict[str, str] | None | t.Type[Sentinel] = Sentinel,
        required_base_class: str | None = None,
    ) -> None:

        self.class_name = class_name
        self.base_class = required_base_class
        self.package = package
        self.subdir = subdir

        if aliases is not Sentinel:
            display.deprecated(
                msg=f"Instantiating {self.type} PluginLoader with aliases is deprecated. {_ALIASES_MSG}",
                version="2.25",
            )
        self._aliases: dict[str, str] = aliases if aliases and aliases is not Sentinel else {}  # type: ignore[assignment]

        if config and not isinstance(config, list):
            config = [config]
        elif not config:
            config = []

        self.config = config

        if class_name not in MODULE_CACHE:
            MODULE_CACHE[class_name] = {}
        if class_name not in PATH_CACHE:
            PATH_CACHE[class_name] = None
        if class_name not in PLUGIN_PATH_CACHE:
            PLUGIN_PATH_CACHE[class_name] = defaultdict(dict)

        # hold dirs added at runtime outside of config
        self._extra_dirs: list[str] = []

        # caches
        self._module_cache = MODULE_CACHE[class_name]
        self._paths = PATH_CACHE[class_name]
        self._plugin_path_cache = PLUGIN_PATH_CACHE[class_name]
        self._plugin_instance_cache: dict[str, tuple[object, PluginLoadContext]] | None = {} if self.subdir == 'vars_plugins' else None

        self._searched_paths: set[str] = set()
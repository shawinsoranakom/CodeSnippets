def get_sysconfig_modules(self) -> Iterable[ModuleInfo]:
        """Get modules defined in Makefile through sysconfig

        MODBUILT_NAMES: modules in *static* block
        MODSHARED_NAMES: modules in *shared* block
        MODDISABLED_NAMES: modules in *disabled* block
        """
        moddisabled = set(sysconfig.get_config_var("MODDISABLED_NAMES").split())
        if self.cross_compiling:
            modbuiltin = set(sysconfig.get_config_var("MODBUILT_NAMES").split())
        else:
            modbuiltin = set(sys.builtin_module_names)

        for key, value in sysconfig.get_config_vars().items():
            if not key.startswith("MODULE_") or not key.endswith("_STATE"):
                continue
            if value not in {"yes", "disabled", "missing", "n/a"}:
                raise ValueError(f"Unsupported value '{value}' for {key}")

            modname = key[7:-6].lower()
            if modname in moddisabled:
                # Setup "*disabled*" rule
                state = ModuleState.DISABLED_SETUP
            elif value in {"disabled", "missing", "n/a"}:
                state = ModuleState(value)
            elif modname in modbuiltin:
                assert value == "yes"
                state = ModuleState.BUILTIN
            else:
                assert value == "yes"
                state = ModuleState.SHARED

            modinfo = ModuleInfo(modname, state)
            logger.debug("Found %s in Makefile", modinfo)
            yield modinfo
def check(self) -> None:
        if not hasattr(_imp, 'create_dynamic'):
            logger.warning(
                ('Dynamic extensions not supported '
                 '(HAVE_DYNAMIC_LOADING not defined)'),
            )
        for modinfo in self.modules:
            logger.debug("Checking '%s' (%s)", modinfo.name, self.get_location(modinfo))
            if modinfo.state == ModuleState.DISABLED:
                self.disabled_configure.append(modinfo)
            elif modinfo.state == ModuleState.DISABLED_SETUP:
                self.disabled_setup.append(modinfo)
            elif modinfo.state == ModuleState.MISSING:
                self.missing.append(modinfo)
            elif modinfo.state == ModuleState.NA:
                self.notavailable.append(modinfo)
            else:
                try:
                    if self.cross_compiling:
                        self.check_module_cross(modinfo)
                    else:
                        self.check_module_import(modinfo)
                except (ImportError, FileNotFoundError):
                    self.rename_module(modinfo)
                    self.failed_on_import.append(modinfo)
                else:
                    if modinfo.state == ModuleState.BUILTIN:
                        self.builtin_ok.append(modinfo)
                    else:
                        assert modinfo.state == ModuleState.SHARED
                        self.shared_ok.append(modinfo)
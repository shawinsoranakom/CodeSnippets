def update_watched_modules(self):
        if self._is_closed:
            return

        if set(sys.modules) != self._cached_sys_modules:
            modules_paths = {
                name: self._exclude_blacklisted_paths(get_module_paths(module))
                for name, module in dict(sys.modules).items()
            }
            self._cached_sys_modules = set(sys.modules)
            self._register_necessary_watchers(modules_paths)
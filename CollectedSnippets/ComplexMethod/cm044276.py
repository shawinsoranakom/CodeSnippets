def _save_modules(
        self,
        modules: str | list[str] | None = None,
        ext_map: dict[str, list[str]] | None = None,
    ):
        """Save the modules."""
        self.console.log("\nWriting modules...")

        if not self.path_list:
            self.console.log("\nThere is nothing to write.")
            return

        MAX_LEN = max([len(path) for path in self.path_list if path != "/"])

        _path_list = (
            [path for path in self.path_list if path in modules]
            if modules
            else self.path_list
        )

        for path in _path_list:
            route = PathHandler.get_route(path, self.route_map)
            # Only create a module if this path doesn't have a direct route
            # This prevents creating sub-router modules for paths like /empty/also_empty
            # when the actual route is /empty/also_empty/{param}
            if route is None:
                code = ModuleBuilder.build(path, ext_map)
                name = PathHandler.build_module_name(path)
                self.console.log(f"({path})", end=" " * (MAX_LEN - len(path)))
                self._write(code, name)
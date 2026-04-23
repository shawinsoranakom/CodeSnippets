def load_by_key_path(
        cls,
        key: str,
        path: str,
        linemap: list[tuple[int, str]] | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> ModuleType:
        if linemap is None:
            linemap = []

        # we only cache when attrs is None
        if attrs is None and path in cls.modules_no_attr:
            return cls.modules_no_attr[path]

        in_toplevel = in_toplevel_process()
        mod = _reload_python_module(key, path, set_sys_modules=in_toplevel)

        # unzip into separate lines/nodes lists
        if in_toplevel:
            cls.linemaps[path] = list(zip(*linemap))

        if attrs is not None:
            for k, v in attrs.items():
                setattr(mod, k, v)

        if in_toplevel:
            # we only cache when attrs is None
            if attrs is None:
                cls.modules_no_attr[path] = mod

            cls.modules.append(mod)
        return mod
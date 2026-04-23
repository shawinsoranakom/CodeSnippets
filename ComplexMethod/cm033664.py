def __init__(
        self,
        path: str,
        module_path: t.Optional[str],
        module_prefix: t.Optional[str],
        base_path: str,
        symlink: t.Optional[bool] = None,
    ) -> None:
        super().__init__()

        if symlink is None:
            symlink = os.path.islink(to_bytes(path.rstrip(os.path.sep)))

        self.name = path
        self.path = path
        self.base_path = base_path + '/' if base_path else None
        self.symlink = symlink

        name, ext = os.path.splitext(os.path.basename(self.path))

        if module_path and is_subdir(path, module_path) and name != '__init__' and ext in MODULE_EXTENSIONS:
            self.module = name[len(module_prefix or ''):].lstrip('_')
            self.modules = (self.module,)
        else:
            self.module = None
            self.modules = tuple()

        aliases = [self.path, self.module]
        parts = self.path.split('/')

        for i in range(1, len(parts)):
            alias = '%s/' % '/'.join(parts[:i])
            aliases.append(alias)

        aliases = [a for a in aliases if a]

        self.aliases = tuple(sorted(aliases))
def base_manager(self):
        base_manager_name = self.base_manager_name
        if not base_manager_name:
            # Get the first parent's base_manager_name if there's one.
            for parent in self.model.mro()[1:]:
                if hasattr(parent, "_meta"):
                    if parent._base_manager.name != "_base_manager":
                        base_manager_name = parent._base_manager.name
                    break

        if base_manager_name:
            try:
                return self.managers_map[base_manager_name]
            except KeyError:
                raise ValueError(
                    "%s has no manager named %r"
                    % (
                        self.object_name,
                        base_manager_name,
                    )
                )

        manager = Manager()
        manager.name = "_base_manager"
        manager.model = self.model
        manager.auto_created = True
        return manager
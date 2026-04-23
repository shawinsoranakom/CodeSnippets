def __setattr__(self, name: str, value: Any) -> None:
        if name == "name" and hasattr(self, "name"):
            m = self.graph.owning_module
            if getattr(m, "_replace_hooks", None):
                if not isinstance(value, str):
                    raise AssertionError(f"Expected value to be str, got {type(value)}")
                for user in self.users:
                    for replace_hook in m._replace_hooks:
                        replace_hook(old=self, new=value, user=user)
        update = False
        if (
            hasattr(self, name)
            and hasattr(self.graph, "_find_nodes_lookup_table")
            and self in self.graph._find_nodes_lookup_table
        ):
            update = True
            self.graph._find_nodes_lookup_table.remove(self)
        object.__setattr__(self, name, value)
        if update:
            self.graph._find_nodes_lookup_table.insert(self)
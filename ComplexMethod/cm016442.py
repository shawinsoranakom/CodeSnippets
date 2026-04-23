def track_type(self, annotation):
        """Track a type annotation and record its module/import info."""
        if annotation is None or annotation is type(None):
            return

        # Skip builtins and typing module types we already import
        type_name = getattr(annotation, "__name__", None)
        if type_name and (
            type_name in self.builtin_types or type_name in self.already_imported
        ):
            return

        # Get module and qualname
        module = getattr(annotation, "__module__", None)
        qualname = getattr(annotation, "__qualname__", type_name or "")

        # Skip types from typing module (they're already imported)
        if module == "typing":
            return

        # Skip UnionType and GenericAlias from types module as they're handled specially
        if module == "types" and type_name in ("UnionType", "GenericAlias"):
            return

        if module and module not in ["builtins", "__main__"]:
            # Store the type info
            if type_name:
                self.discovered_types[type_name] = (module, qualname)
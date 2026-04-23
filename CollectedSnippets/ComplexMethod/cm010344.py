def whichmodule(self, obj: Any, name: str) -> str:
        """Find the module name an object belongs to.

        This should be considered internal for end-users, but developers of
        an importer can override it to customize the behavior.

        Taken from pickle.py, but modified to exclude the search into sys.modules
        """
        module_name = getattr(obj, "__module__", None)
        if module_name is not None:
            return module_name

        # Protect the iteration by using a list copy of self.modules against dynamic
        # modules that trigger imports of other modules upon calls to getattr.
        for module_name, module in self.modules.copy().items():
            if (
                module_name == "__main__"
                or module_name == "__mp_main__"  # bpo-42406
                or module is None
            ):
                continue
            try:
                if _getattribute(module, name)[0] is obj:
                    return module_name
            except AttributeError:
                pass

        return "__main__"
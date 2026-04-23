def _handle_fromlist(self, module, fromlist, *, recursive=False):
        """Figure out what __import__ should return.

        The import_ parameter is a callable which takes the name of module to
        import. It is required to decouple the function from assuming importlib's
        import implementation is desired.

        """
        module_name = demangle(module.__name__)
        # The hell that is fromlist ...
        # If a package was imported, try to import stuff from fromlist.
        if hasattr(module, "__path__"):
            for x in fromlist:
                if not isinstance(x, str):
                    if recursive:
                        where = module_name + ".__all__"
                    else:
                        where = "``from list''"
                    raise TypeError(
                        f"Item in {where} must be str, not {type(x).__name__}"
                    )
                elif x == "*":
                    if not recursive and hasattr(module, "__all__"):
                        self._handle_fromlist(module, module.__all__, recursive=True)
                elif not hasattr(module, x):
                    from_name = f"{module_name}.{x}"
                    try:
                        self._gcd_import(from_name)
                    except ModuleNotFoundError as exc:
                        # Backwards-compatibility dictates we ignore failed
                        # imports triggered by fromlist for modules that don't
                        # exist.
                        if (
                            exc.name == from_name
                            and self.modules.get(from_name, _NEEDS_LOADING) is not None
                        ):
                            continue
                        raise
        return module
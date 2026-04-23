def get_name(self, obj: Any, name: str | None = None) -> tuple[str, str]:
        """Given an object, return a name that can be used to retrieve the
        object from this environment.

        Args:
            obj: An object to get the module-environment-relative name for.
            name: If set, use this name instead of looking up __name__ or __qualname__ on `obj`.
                This is only here to match how Pickler handles __reduce__ functions that return a string,
                don't use otherwise.
        Returns:
            A tuple (parent_module_name, attr_name) that can be used to retrieve `obj` from this environment.
            Use it like:
                mod = importer.import_module(parent_module_name)
                obj = getattr(mod, attr_name)

        Raises:
            ObjNotFoundError: we couldn't retrieve `obj by name.
            ObjMisMatchError: we found a different object with the same name as `obj`.
        """
        if name is None and obj and _Pickler.dispatch.get(type(obj)) is None:
            # Honor the string return variant of __reduce__, which will give us
            # a global name to search for in this environment.
            # TODO: I guess we should do copyreg too?
            reduce = getattr(obj, "__reduce__", None)
            if reduce is not None:
                try:
                    rv = reduce()
                    if isinstance(rv, str):
                        name = rv
                except Exception:
                    pass
        if name is None:
            name = getattr(obj, "__qualname__", None)
        if name is None:
            name = obj.__name__

        orig_module_name = self.whichmodule(obj, name)
        # Demangle the module name before importing. If this obj came out of a
        # PackageImporter, `__module__` will be mangled. See mangling.md for
        # details.
        module_name = demangle(orig_module_name)

        # Check that this name will indeed return the correct object
        try:
            module = self.import_module(module_name)
            if sys.version_info >= (3, 14):
                # pickle._getatribute signature changes in 3.14
                # to take iterable and return just one object
                obj2 = _getattribute(module, name.split("."))
            else:
                obj2, _ = _getattribute(module, name)
        except (ImportError, KeyError, AttributeError):
            raise ObjNotFoundError(
                f"{obj} was not found as {module_name}.{name}"
            ) from None

        if obj is obj2:
            return module_name, name

        def get_obj_info(obj):
            if name is None:
                raise AssertionError("name must not be None")
            module_name = self.whichmodule(obj, name)
            is_mangled_ = is_mangled(module_name)
            location = (
                get_mangle_prefix(module_name)
                if is_mangled_
                else "the current Python environment"
            )
            importer_name = (
                f"the importer for {get_mangle_prefix(module_name)}"
                if is_mangled_
                else "'sys_importer'"
            )
            return module_name, location, importer_name

        obj_module_name, obj_location, obj_importer_name = get_obj_info(obj)
        obj2_module_name, obj2_location, obj2_importer_name = get_obj_info(obj2)
        msg = (
            f"\n\nThe object provided is from '{obj_module_name}', "
            f"which is coming from {obj_location}."
            f"\nHowever, when we import '{obj2_module_name}', it's coming from {obj2_location}."
            "\nTo fix this, make sure this 'PackageExporter's importer lists "
            f"{obj_importer_name} before {obj2_importer_name}."
        )
        raise ObjMismatchError(msg)
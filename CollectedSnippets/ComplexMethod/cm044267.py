def _trigger_command_output_callbacks(cls, route: str, obbject: OBBject) -> None:
        """Trigger command output callbacks for extensions."""
        loader = ExtensionLoader()
        callbacks = loader.on_command_output_callbacks
        if not callbacks:
            return

        # For each extension registered for all routes or the specific route,
        # we call its accessor on the OBBject.
        # We check if the accessor is immutable or not to decide whether to pass
        # a copy of the OBBject or the original one.
        # We set the _extension_modified attribute to True if any extension
        # mutates the OBBject so we can pass this information to the interface.
        # We also set the _results_only attribute to True if any extension
        # indicates that only results should be returned.
        results_only = False
        executed_keys: set[str] = set()
        ordered_extensions: list = []
        all_on_command_output_exts: list = []

        def _extension_key(ext) -> str:
            if key := getattr(ext, "identifier", None):
                return str(key)
            if path := getattr(ext, "import_path", None):
                return f"{path}:{getattr(ext, 'name', id(ext))}"
            return str(getattr(ext, "name", id(ext)))

        def _clone_for_immutable(source: OBBject) -> OBBject | None:
            try:
                new_source = source.model_copy()
                new_source = OBBject.model_validate(source.model_dump())
                return source.model_validate(new_source)
            except Exception as e:
                warn(
                    "Skipped immutable callback because the OBBject "
                    f"could not be duplicated. {e}",
                    OpenBBWarning,
                )
                return None

        for ext_list in callbacks.values():
            all_on_command_output_exts.extend(ext_list)

        for ext in callbacks.get("*", []):
            key = _extension_key(ext)
            if key not in executed_keys:
                executed_keys.add(key)
                ordered_extensions.append(ext)

        for ext in callbacks.get(route, []):
            key = _extension_key(ext)
            if key not in executed_keys:
                executed_keys.add(key)
                ordered_extensions.append(ext)

        try:
            for ext in ordered_extensions:
                if ext.results_only is True:
                    results_only = True

                if ext.command_output_paths and route not in ext.command_output_paths:
                    continue

                accessors: set = getattr(type(obbject), "accessors", set())
                if ext.name not in accessors:
                    continue

                descriptor = type(obbject).__dict__.get(ext.name)
                if not isinstance(descriptor, CachedAccessor):
                    continue

                factory = descriptor._accessor  # type: ignore  # pylint: disable=W0212

                target = _clone_for_immutable(obbject) if ext.immutable else obbject

                if target is None:
                    continue

                if iscoroutinefunction(factory):
                    run_async(factory, target)
                else:
                    result = factory(target)
                    if callable(result):
                        result()

                if ext.immutable is False:
                    object.__setattr__(obbject, "_extension_modified", True)

            if results_only is True:
                object.__setattr__(obbject, "_results_only", True)
                object.__setattr__(obbject, "_extension_modified", True)

        except Exception as e:
            raise OpenBBError(e) from e

        for ext in all_on_command_output_exts:
            if ext.name in type(obbject).__dict__:
                object.__setattr__(
                    obbject,
                    ext.name,
                    "Accessor is not callable outside of function execution.",
                )
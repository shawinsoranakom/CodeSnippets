def save_global(self, obj, name=None):
        # ruff: noqa: F841
        # unfortunately the pickler code is factored in a way that
        # forces us to copy/paste this function. The only change is marked
        # CHANGED below.
        write = self.write  # type: ignore[attr-defined]
        memo = self.memo  # type: ignore[attr-defined]

        # CHANGED: import module from module environment instead of __import__
        try:
            module_name, name = self.importer.get_name(obj, name)
        except (ObjNotFoundError, ObjMismatchError) as err:
            raise PicklingError(f"Can't pickle {obj}: {str(err)}") from err

        module = self.importer.import_module(module_name)
        if sys.version_info >= (3, 14):
            # pickle._getattribute signature changes in 3.14
            # to take iterable and return just the object (not tuple)
            # We need to get the parent object that contains the attribute
            name_parts = name.split(".")
            if "<locals>" in name_parts:
                raise PicklingError(f"Can't pickle local object {obj!r}")
            if len(name_parts) == 1:
                parent = module
            else:
                parent = _getattribute(module, name_parts[:-1])
        else:
            _, parent = _getattribute(module, name)
        # END CHANGED

        if self.proto >= 2:  # type: ignore[attr-defined]
            code = _extension_registry.get((module_name, name))
            if code:
                if code <= 0:
                    raise AssertionError(
                        f"expected positive extension code, got {code}"
                    )
                if code <= 0xFF:
                    write(EXT1 + pack("<B", code))
                elif code <= 0xFFFF:
                    write(EXT2 + pack("<H", code))
                else:
                    write(EXT4 + pack("<i", code))
                return
        lastname = name.rpartition(".")[2]
        if parent is module:
            name = lastname
        # Non-ASCII identifiers are supported only with protocols >= 3.
        if self.proto >= 4:  # type: ignore[attr-defined]
            self.save(module_name)  # type: ignore[attr-defined]
            self.save(name)  # type: ignore[attr-defined]
            write(STACK_GLOBAL)
        elif parent is not module:
            self.save_reduce(getattr, (parent, lastname))  # type: ignore[attr-defined]
        elif self.proto >= 3:  # type: ignore[attr-defined]
            write(
                GLOBAL
                + bytes(module_name, "utf-8")
                + b"\n"
                + bytes(name, "utf-8")
                + b"\n"
            )
        else:
            if self.fix_imports:  # type: ignore[attr-defined]
                r_name_mapping = _compat_pickle.REVERSE_NAME_MAPPING
                r_import_mapping = _compat_pickle.REVERSE_IMPORT_MAPPING
                if (module_name, name) in r_name_mapping:
                    module_name, name = r_name_mapping[(module_name, name)]
                elif module_name in r_import_mapping:
                    module_name = r_import_mapping[module_name]
            try:
                write(
                    GLOBAL
                    + bytes(module_name, "ascii")
                    + b"\n"
                    + bytes(name, "ascii")
                    + b"\n"
                )
            except UnicodeEncodeError as exc:
                raise PicklingError(
                    f"can't pickle global identifier '{module}.{name}' using "
                    f"pickle protocol {self.proto:d}"  # type: ignore[attr-defined]
                ) from exc

        self.memoize(obj)
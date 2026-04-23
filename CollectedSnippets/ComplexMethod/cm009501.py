def __call__(self, value: dict[str, Any]) -> Any:
        """Revive the value.

        Args:
            value: The value to revive.

        Returns:
            The revived value.

        Raises:
            ValueError: If the namespace is invalid.
            ValueError: If trying to deserialize something that cannot
                be deserialized in the current version of langchain-core.
            NotImplementedError: If the object is not implemented and
                `ignore_unserializable_fields` is False.
        """
        if (
            value.get("lc") == 1
            and value.get("type") == "secret"
            and value.get("id") is not None
        ):
            [key] = value["id"]
            if key in self.secrets_map:
                return self.secrets_map[key]
            if self.secrets_from_env and key in os.environ and os.environ[key]:
                return os.environ[key]
            return None

        if (
            value.get("lc") == 1
            and value.get("type") == "not_implemented"
            and value.get("id") is not None
        ):
            if self.ignore_unserializable_fields:
                return None
            msg = (
                "Trying to load an object that doesn't implement "
                f"serialization: {value}"
            )
            raise NotImplementedError(msg)

        if (
            value.get("lc") == 1
            and value.get("type") == "constructor"
            and value.get("id") is not None
        ):
            [*namespace, name] = value["id"]
            mapping_key = tuple(value["id"])

            if (
                self.allowed_class_paths is not None
                and mapping_key not in self.allowed_class_paths
            ):
                msg = (
                    f"Deserialization of {mapping_key!r} is not allowed. "
                    "The default (allowed_objects='core') only permits core "
                    "langchain-core classes. To allow trusted partner integrations, "
                    "use allowed_objects='all'. Alternatively, pass an explicit list "
                    "of allowed classes via allowed_objects=[...]. "
                    "See langchain_core.load.mapping for the full allowlist."
                )
                raise ValueError(msg)

            if (
                namespace[0] not in self.valid_namespaces
                # The root namespace ["langchain"] is not a valid identifier.
                or namespace == ["langchain"]
            ):
                msg = f"Invalid namespace: {value}"
                raise ValueError(msg)
            # Determine explicit import path
            if mapping_key in self.import_mappings:
                import_path = self.import_mappings[mapping_key]
                # Split into module and name
                import_dir, name = import_path[:-1], import_path[-1]
            elif namespace[0] in DISALLOW_LOAD_FROM_PATH:
                msg = (
                    "Trying to deserialize something that cannot "
                    "be deserialized in current version of langchain-core: "
                    f"{mapping_key}."
                )
                raise ValueError(msg)
            else:
                # Otherwise, treat namespace as path.
                import_dir = namespace

            # Validate import path is in trusted namespaces before importing
            if import_dir[0] not in self.valid_namespaces:
                msg = f"Invalid namespace: {value}"
                raise ValueError(msg)

            # We don't need to recurse on kwargs
            # as json.loads will do that for us.
            kwargs = value.get("kwargs", {})

            # Run class-specific validators before the general init_validator.
            # These run before importing to fail fast on security violations.
            if mapping_key in CLASS_INIT_VALIDATORS:
                CLASS_INIT_VALIDATORS[mapping_key](mapping_key, kwargs)

            # Also run general init_validator (e.g., jinja2 blocking)
            if self.init_validator is not None:
                self.init_validator(mapping_key, kwargs)

            mod = importlib.import_module(".".join(import_dir))

            cls = getattr(mod, name)

            # The class must be a subclass of Serializable.
            if not issubclass(cls, Serializable):
                msg = f"Invalid namespace: {value}"
                raise ValueError(msg)

            return cls(**kwargs)

        return value
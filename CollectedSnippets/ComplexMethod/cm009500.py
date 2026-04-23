def __init__(
        self,
        allowed_objects: Iterable[AllowedObject] | Literal["all", "core"] = "core",
        secrets_map: dict[str, str] | None = None,
        valid_namespaces: list[str] | None = None,
        secrets_from_env: bool = False,  # noqa: FBT001,FBT002
        additional_import_mappings: dict[tuple[str, ...], tuple[str, ...]]
        | None = None,
        *,
        ignore_unserializable_fields: bool = False,
        init_validator: InitValidator | None = default_init_validator,
    ) -> None:
        """Initialize the reviver.

        Args:
            allowed_objects: Allowlist of classes that can be deserialized.
                - `'core'` (default): Allow classes defined in the serialization
                    mappings for `langchain_core`.
                - `'all'`: Allow classes defined in the serialization mappings.

                    This includes core LangChain types (messages, prompts, documents,
                    etc.) and trusted partner integrations. See
                    `langchain_core.load.mapping` for the full list.
                - Explicit list of classes: Only those specific classes are allowed.
            secrets_map: A map of secrets to load.

                Only include the specific secrets the serialized object
                requires. If a secret is not found in the map, it will be loaded
                from the environment if `secrets_from_env` is `True`.
            valid_namespaces: Additional namespaces (modules) to allow during
                deserialization, beyond the default trusted namespaces.
            secrets_from_env: Whether to load secrets from the environment.

                A crafted payload can name arbitrary environment variables in
                its `secret` fields, so enabling this on untrusted data can leak
                sensitive values. Keep this `False` (the default) unless the
                serialized data is fully trusted.
            additional_import_mappings: A dictionary of additional namespace mappings.

                You can use this to override default mappings or add new mappings.

                When `allowed_objects` is `None` (using defaults), paths from these
                mappings are also added to the allowed class paths.
            ignore_unserializable_fields: Whether to ignore unserializable fields.
            init_validator: Optional callable to validate kwargs before instantiation.

                If provided, this function is called with `(class_path, kwargs)` where
                `class_path` is the class path tuple and `kwargs` is the kwargs dict.
                The validator should raise an exception if the object should not be
                deserialized, otherwise return `None`.

                Defaults to `default_init_validator` which blocks jinja2 templates.
        """
        self.secrets_from_env = secrets_from_env
        self.secrets_map = secrets_map or {}
        # By default, only support langchain, but user can pass in additional namespaces
        self.valid_namespaces = (
            [*DEFAULT_NAMESPACES, *valid_namespaces]
            if valid_namespaces
            else DEFAULT_NAMESPACES
        )
        self.additional_import_mappings = additional_import_mappings or {}
        self.import_mappings = (
            {
                **ALL_SERIALIZABLE_MAPPINGS,
                **self.additional_import_mappings,
            }
            if self.additional_import_mappings
            else ALL_SERIALIZABLE_MAPPINGS
        )
        # Compute allowed class paths:
        # - "all" -> use default paths from mappings (+ additional_import_mappings)
        # - Explicit list -> compute from those classes
        if allowed_objects in ("all", "core"):
            self.allowed_class_paths: set[tuple[str, ...]] | None = (
                _get_default_allowed_class_paths(
                    cast("Literal['all', 'core']", allowed_objects)
                ).copy()
            )
            # Add paths from additional_import_mappings to the defaults
            if self.additional_import_mappings:
                for key, value in self.additional_import_mappings.items():
                    self.allowed_class_paths.add(key)
                    self.allowed_class_paths.add(value)
        else:
            self.allowed_class_paths = _compute_allowed_class_paths(
                cast("Iterable[AllowedObject]", allowed_objects), self.import_mappings
            )
        self.ignore_unserializable_fields = ignore_unserializable_fields
        self.init_validator = init_validator
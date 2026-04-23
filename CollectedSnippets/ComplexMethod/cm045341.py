def load_component(
        cls, model: ComponentModel | Dict[str, Any], expected: Type[ExpectedType] | None = None
    ) -> Self | ExpectedType:
        """Load a component from a model. Intended to be used with the return type of :py:meth:`autogen_core.ComponentConfig.dump_component`.

        Example:

            .. code-block:: python

                from autogen_core import ComponentModel
                from autogen_core.models import ChatCompletionClient

                component: ComponentModel = ...  # type: ignore

                model_client = ChatCompletionClient.load_component(component)

        Args:
            model (ComponentModel): The model to load the component from.

        Returns:
            Self: The loaded component.

        Args:
            model (ComponentModel): _description_
            expected (Type[ExpectedType] | None, optional): Explicit type only if used directly on ComponentLoader. Defaults to None.

        Raises:
            ValueError: If the provider string is invalid.
            TypeError: Provider is not a subclass of ComponentConfigImpl, or the expected type does not match.

        Returns:
            Self | ExpectedType: The loaded component.
        """

        # Use global and add further type checks

        if isinstance(model, dict):
            loaded_model = ComponentModel(**model)
        else:
            loaded_model = model

        # First, do a look up in well known providers
        if loaded_model.provider in WELL_KNOWN_PROVIDERS:
            loaded_model.provider = WELL_KNOWN_PROVIDERS[loaded_model.provider]

        output = loaded_model.provider.rsplit(".", maxsplit=1)
        if len(output) != 2:
            raise ValueError("Invalid")

        module_path, class_name = output

        trusted = _get_trusted_namespaces()
        # Also allow test modules (pytest convention) to load components
        module_name = module_path.rsplit(".", maxsplit=1)[-1]
        is_test_module = module_name.startswith("test_") or module_path.startswith("test_")
        if not is_test_module and not any(
            module_path.startswith(ns) or module_path == ns.rstrip(".") for ns in trusted
        ):
            raise ValueError(
                f"Provider module '{module_path}' is not in a trusted namespace. "
                f"Allowed namespaces by default: autogen_core, autogen_agentchat, autogen_ext, "
                f"autogen_studio, autogenstudio. "
                f"To allow additional namespaces, set the AUTOGEN_ALLOWED_PROVIDER_NAMESPACES "
                f"environment variable to a comma-separated list "
                f"(e.g. AUTOGEN_ALLOWED_PROVIDER_NAMESPACES=mycompany_agents,mypackage)."
            )

        module = importlib.import_module(module_path)
        component_class = module.__getattribute__(class_name)

        if not is_component_class(component_class):
            raise TypeError("Invalid component class")

        # We need to check the schema is valid
        if not hasattr(component_class, "component_config_schema"):
            raise AttributeError("component_config_schema not defined")

        if not hasattr(component_class, "component_type"):
            raise AttributeError("component_type not defined")

        loaded_config_version = loaded_model.component_version or component_class.component_version
        if loaded_config_version < component_class.component_version:
            try:
                instance = component_class._from_config_past_version(loaded_model.config, loaded_config_version)  # type: ignore
            except NotImplementedError as e:
                raise NotImplementedError(
                    f"Tried to load component {component_class} which is on version {component_class.component_version} with a config on version {loaded_config_version} but _from_config_past_version is not implemented"
                ) from e
        else:
            schema = component_class.component_config_schema  # type: ignore
            validated_config = schema.model_validate(loaded_model.config)

            # We're allowed to use the private method here
            instance = component_class._from_config(validated_config)  # type: ignore

        if expected is None and not isinstance(instance, cls):
            raise TypeError("Expected type does not match")
        elif expected is None:
            return cast(Self, instance)
        elif not isinstance(instance, expected):
            raise TypeError("Expected type does not match")
        else:
            return cast(ExpectedType, instance)
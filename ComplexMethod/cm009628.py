def wrapper(cls: type[BaseModel], values: dict[str, Any]) -> Any:
            """Decorator to run a function before model initialization.

            Args:
                cls: The model class.
                values: The values to initialize the model with.

            Returns:
                The values to initialize the model with.
            """
            # Insert default values
            fields = cls.model_fields
            for name, field_info in fields.items():
                # Check if allow_population_by_field_name is enabled
                # If yes, then set the field name to the alias
                if (
                    hasattr(cls, "Config")
                    and hasattr(cls.Config, "allow_population_by_field_name")
                    and cls.Config.allow_population_by_field_name
                    and field_info.alias in values
                ):
                    values[name] = values.pop(field_info.alias)
                if (
                    hasattr(cls, "model_config")
                    and cls.model_config.get("populate_by_name")
                    and field_info.alias in values
                ):
                    values[name] = values.pop(field_info.alias)

                if (
                    name not in values or values[name] is None
                ) and not field_info.is_required():
                    if field_info.default_factory is not None:
                        values[name] = field_info.default_factory()  # type: ignore[call-arg]
                    else:
                        values[name] = field_info.default

            # Call the decorated function
            return func(cls, values)
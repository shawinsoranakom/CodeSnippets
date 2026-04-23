def config_schema(self, *, include: Sequence[str] | None = None) -> type[BaseModel]:
        """The type of config this `Runnable` accepts specified as a Pydantic model.

        To mark a field as configurable, see the `configurable_fields`
        and `configurable_alternatives` methods.

        Args:
            include: A list of fields to include in the config schema.

        Returns:
            A Pydantic model that can be used to validate config.

        """
        include = include or []
        config_specs = self.config_specs
        configurable = (
            create_model_v2(
                "Configurable",
                field_definitions={
                    spec.id: (
                        spec.annotation,
                        Field(
                            spec.default, title=spec.name, description=spec.description
                        ),
                    )
                    for spec in config_specs
                },
            )
            if config_specs
            else None
        )

        # Many need to create a typed dict instead to implement NotRequired!
        all_fields = {
            **({"configurable": (configurable, None)} if configurable else {}),
            **{
                field_name: (field_type, None)
                for field_name, field_type in get_type_hints(RunnableConfig).items()
                if field_name in [i for i in include if i != "configurable"]
            },
        }
        return create_model_v2(self.get_name("Config"), field_definitions=all_fields)
def get_input_schema(self, config: RunnableConfig | None = None) -> type[BaseModel]:
        """Get the input schema of the `Runnable`.

        Args:
            config: The config to use.

        Returns:
            The input schema of the `Runnable`.

        """
        if all(
            s.get_input_schema(config).model_json_schema().get("type", "object")
            == "object"
            for s in self.steps__.values()
        ):
            for step in self.steps__.values():
                fields = step.get_input_schema(config).model_fields
                root_field = fields.get("root")
                if root_field is not None and root_field.annotation != Any:
                    return super().get_input_schema(config)

            # This is correct, but pydantic typings/mypy don't think so.
            return create_model_v2(
                self.get_name("Input"),
                field_definitions={
                    k: (v.annotation, v.default)
                    for step in self.steps__.values()
                    for k, v in step.get_input_schema(config).model_fields.items()
                    if k != "__root__"
                },
            )

        return super().get_input_schema(config)
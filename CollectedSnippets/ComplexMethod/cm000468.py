def _generate_schema(
        *props: tuple[type[AgentInputBlock.Input] | type[AgentOutputBlock.Input], dict],
    ) -> dict[str, Any]:
        schema_fields: list[AgentInputBlock.Input | AgentOutputBlock.Input] = []
        for type_class, input_default in props:
            try:
                schema_fields.append(type_class.model_construct(**input_default))
            except Exception as e:
                logger.error(f"Invalid {type_class}: {input_default}, {e}")

        try:
            return {
                "type": "object",
                "properties": {
                    p.name: {
                        **{
                            k: v
                            for k, v in p.generate_schema().items()
                            if k not in ["description", "default"]
                        },
                        "secret": p.secret,
                        # Default value has to be set for advanced fields.
                        "advanced": p.advanced and p.value is not None,
                        "title": p.title or p.name,
                        **({"description": p.description} if p.description else {}),
                        **({"default": p.value} if p.value is not None else {}),
                    }
                    for p in schema_fields
                },
                "required": [p.name for p in schema_fields if p.value is None],
            }
        except AttributeError as e:
            raise ValueError(str(e)) from e
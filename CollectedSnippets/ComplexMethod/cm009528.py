def _seq_output_schema(
    steps: list[Runnable[Any, Any]], config: RunnableConfig | None
) -> type[BaseModel]:
    # Import locally to prevent circular import
    from langchain_core.runnables.passthrough import (  # noqa: PLC0415
        RunnableAssign,
        RunnablePick,
    )

    last = steps[-1]
    if len(steps) == 1:
        return last.get_input_schema(config)
    if isinstance(last, RunnableAssign):
        mapper_output_schema = last.mapper.get_output_schema(config)
        prev_output_schema = _seq_output_schema(steps[:-1], config)
        if not issubclass(prev_output_schema, RootModel):
            # it's a dict as expected
            return create_model_v2(
                "RunnableSequenceOutput",
                field_definitions={
                    **{
                        k: (v.annotation, v.default)
                        for k, v in prev_output_schema.model_fields.items()
                    },
                    **{
                        k: (v.annotation, v.default)
                        for k, v in mapper_output_schema.model_fields.items()
                    },
                },
            )
    elif isinstance(last, RunnablePick):
        prev_output_schema = _seq_output_schema(steps[:-1], config)
        if not issubclass(prev_output_schema, RootModel):
            # it's a dict as expected
            if isinstance(last.keys, list):
                return create_model_v2(
                    "RunnableSequenceOutput",
                    field_definitions={
                        k: (v.annotation, v.default)
                        for k, v in prev_output_schema.model_fields.items()
                        if k in last.keys
                    },
                )
            field = prev_output_schema.model_fields[last.keys]
            return create_model_v2(
                "RunnableSequenceOutput", root=(field.annotation, field.default)
            )

    return last.get_output_schema(config)
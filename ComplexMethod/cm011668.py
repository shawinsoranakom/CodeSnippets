def set_tracing_context_output_strides(
    example_inputs: Sequence[Any], compiled_graph: CompiledFxGraph
) -> None:
    # Return the output strides to the caller via TracingContext
    context = torch._guards.TracingContext.try_get()
    if context is not None and context.output_strides is not None:
        assert len(context.output_strides) == 0
        shape_env = shape_env_from_inputs(example_inputs)
        assert compiled_graph.output_strides is not None
        for exprs in compiled_graph.output_strides:
            if exprs is None:
                context.output_strides.append(None)
            else:
                fakify_first_call = False
                if ctx := torch._guards.TracingContext.try_get():
                    fakify_first_call = ctx.fakify_first_call

                def map_expr(e: Any) -> float | int | SymInt | SymFloat | SymBool:
                    if shape_env is None:
                        return int(e)
                    if fakify_first_call:
                        return shape_env.deserialize_symexpr(e)
                    return shape_env.evaluate_symexpr(e)

                context.output_strides.append(
                    tuple(map_expr(e) for e in exprs)  # type: ignore[misc]
                )
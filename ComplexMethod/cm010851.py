def _backward_epilogue_functional(
    metadata: ViewAndMutationMeta,
    maybe_subclass_metadata: SubclassMeta | None,
    out: Any,
    *,
    ctx_opaque_objects: Sequence[Any] = (),
    make_subclass_override: Callable[..., Any] | None = None,
    codegen_wrap_fn: Callable[..., Any] | None = None,
) -> tuple[Any, ...]:
    # Toss out the backward output tokens
    num_bw_tokens = metadata.num_backward_tokens
    if num_bw_tokens > 0:
        out = out[:-num_bw_tokens]

    # TODO: replace this with FunctionalizedRngRuntimeWrapper.post_compile
    out = FunctionalizedRngRuntimeWrapper()._functionalized_rng_runtime_epilogue(
        metadata, out, offset_index=len(out) - 1
    )
    out = tuple(out)

    # Replace compile-time opaque constants in the backward output with the
    # real runtime opaques saved from the forward pass. During joint graph
    # tracing, backward output opaques come from tangent constants (baked at
    # compile time). At runtime we need the actual opaque objects that were
    # saved for backward from the forward pass.
    if ctx_opaque_objects:
        opaque_iter = iter(ctx_opaque_objects)
        out = tuple(
            next(opaque_iter) if isinstance(v, FakeScriptObject) else v for v in out
        )
        remaining = list(opaque_iter)
        if remaining:
            raise AssertionError(
                f"ctx_opaque_objects had {len(remaining)} leftover entries "
                "(expected all to be consumed by FakeScriptObject slots in backward output)"
            )

    # TODO: figure out how to refactor the backward properly so I can use aot_dispatch_subclass_wrapper() here.
    if maybe_subclass_metadata is not None:
        if maybe_subclass_metadata.grad_input_metas is None:
            raise AssertionError("grad_input_metas must not be None")
        if codegen_wrap_fn is not None and make_subclass_override is None:
            return codegen_wrap_fn(out)
        outs_wrapped = wrap_tensor_subclasses(
            out,
            subclass_metas=maybe_subclass_metadata.grad_input_metas,
            included_subclass_symints=True,
            is_runtime=True,
            make_subclass_override=make_subclass_override,
        )
        return outs_wrapped
    return out
def fakify(
    mode: FakeTensorMode,
    kp: KeyPath,
    t: Any,
    t_constraints: dict[int, dict[int, Constraint]],
    sources: dict[tuple[int, int], list[Source]],
    sourced_prefixes: _KeyPathTrie | None = None,
):
    source = key_path_to_source(kp, sourced_prefixes=sourced_prefixes)
    if (
        _is_constant_argument(t)
        or isinstance(t, (torch.ScriptObject, torch.nn.Module))
        or is_opaque_value(t)
    ):
        return t

    if isinstance(t, _IntWrapper):
        if t.dynamism is not None and t.dynamism.type in (  # type: ignore[union-attr]
            _DimHintType.DYNAMIC,
            _DimHintType.AUTO,
        ):
            symint = mode.shape_env.create_unspecified_symint_and_symbol(  # type: ignore[union-attr]
                t.val, source, DimDynamic.DYNAMIC
            )
            context = (
                SymIntSymbolicContext(
                    constraint=RelaxedUnspecConstraint(warn_only=False)
                )
                if t.dynamism.type == _DimHintType.DYNAMIC  # type: ignore[union-attr]
                else None
            )
            mode.shape_env.tracked_fakes.append(  # type: ignore[union-attr]
                TrackedFake(symint, source, context)
            )
            return symint
        else:
            return t.val

    if not isinstance(t, torch.Tensor):
        raise ValueError(
            f"Unsupported input type {type(t)}. "
            "Export only supports pytree containers of basic types (Tensor, int, float, ...) as input. "
            "To register a custom dataclass, use torch.export.register_dataclass. "
            "To register a custom container type, use torch.utils._pytree.register_pytree_node. "
            "To register a constant input, use torch.utils._pytree.register_constant"
        )

    # Create symbolic context (handles subclass recursion internally)
    symbolic_context = _create_symbolic_context_for_tensor(
        t, source, t_constraints, sources, mode
    )

    fake = mode.from_tensor(t, source=source, symbolic_context=symbolic_context)
    mode.shape_env.tracked_fakes.append(TrackedFake(fake, source, symbolic_context))  # type: ignore[union-attr]
    return fake
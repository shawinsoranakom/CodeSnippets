def _process_equalities(
    constraint: Constraint,
    get_sources: Callable[[int, int], list["Source"]],
    shape_env: "ShapeEnv",
    names: dict[str, tuple[int, int]],
    source_pairs: list[tuple["Source", "Source"]],
    derived_equalities: list[tuple["Source", Union["Source", "Symbol"], Callable]],
    phantom_symbols: dict[str, "Symbol"],
    relaxed_sources: set["Source"],
):
    """
    Updates `source_pairs`, `derived_equalities`, and `phantom_symbols` (which become
    fields of `EqualityConstraint`) based on a given input `constraint`.
    """

    sources = get_sources(constraint.t_id, constraint.dim)
    if not sources:  # empty sources due to unused shapes
        return

    source, *other_sources = sources
    # When t.size()[dim] maps to src0, src1, ..., srcN, we add
    # constraints that make src0 "equal" to src1, ..., srcN.
    source_pairs.extend((source, other_source) for other_source in other_sources)
    if isinstance(constraint, _Constraint):
        if constraint.name in names:
            shared_t_id, shared_dim = names[constraint.name]
            other_sources = get_sources(shared_t_id, shared_dim)
            source_pairs.extend(
                (source, other_source) for other_source in other_sources
            )
        else:
            names[constraint.name] = (constraint.t_id, constraint.dim)
    elif isinstance(constraint, _DerivedConstraint):
        # branch based on the root of the _DerivedConstraint
        if not isinstance(constraint.root, _PhantomRoot):
            # either root points to an input source
            root = get_sources(constraint.root.t_id, constraint.root.dim)[0]
        else:
            # or root points to a phantom symbol
            if constraint.root.name in phantom_symbols:
                root = phantom_symbols[constraint.root.name]
            else:
                # create a phantom symbol in the shape env based on the _PhantomRoot
                root = shape_env.create_symbol(
                    val=constraint.root.val,
                    source=torch._dynamo.source.ConstantSource(constraint.root.name),
                    dynamic_dim=torch.fx.experimental.symbolic_shapes.DimDynamic.DYNAMIC,
                    constraint_dim=constraint.root.constraint_range,
                )
                phantom_symbols[constraint.root.name] = root

        fn = constraint.fn
        # A derived equality (source, root, fn) informally corresponds to source = fn(root).
        # Here source describes an input and root might describe another input or a phantom symbol.
        derived_equalities.append((source, root, fn))
    elif isinstance(constraint, _RelaxedConstraint):
        relaxed_sources.add(source)
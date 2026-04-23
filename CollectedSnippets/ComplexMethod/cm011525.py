def _extract_rules_from_op_strategy(
    op_strategy: Any,
    input_shapes: tuple[tuple[int, ...], ...],
    output_shapes: tuple[tuple[int, ...], ...],
) -> set[ComboKey]:
    """Extract normalized sharding rules from an OpStrategy.

    Called during rule comparison to collect DTensor's claimed-valid placement
    combinations. These are compared against ground truth (brute-force
    validation) to find false positives (DTensor claims valid but wrong) and
    false negatives (valid but DTensor has no rule).
    """
    rules: set[ComboKey] = set()
    if not isinstance(op_strategy, OpStrategy):
        return rules
    for spec in op_strategy.strategies:
        if spec.input_specs is None:
            continue
        if isinstance(spec.output_specs, tuple):
            output_plcs: list[Placement] = []
            has_none = False
            for out_spec in spec.output_specs:
                if out_spec is None:
                    # None means the output placement is undefined for this
                    # strategy (e.g. indices under P(max) reduction). Skip it.
                    has_none = True
                    break
                output_plcs.append(out_spec.placements[0])
            if has_none:
                continue
        else:
            # Single DTensorSpec — the propagator duplicates it for all
            # outputs of multi-output ops, so we do the same here.
            output_plcs = [spec.output_spec.placements[0]] * len(output_shapes)
        input_plcs = tuple(s.placements[0] for s in spec.input_specs)
        rule_key: ComboKey = (
            tuple(str(p) for p in input_plcs),
            tuple(str(p) for p in output_plcs),
        )
        normalized_rule = normalize_combo_key(rule_key, input_shapes, output_shapes)
        if not is_fully_replicated(
            tuple(parse_placement(p) or Replicate() for p in normalized_rule[0])
        ):
            rules.add(normalized_rule)
    return rules
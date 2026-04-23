def _propagate_use_strided_shard_flag(
    op_strategy: OpStrategy,
    op_schema: OpSchema,
) -> None:
    """Propagate use_strided_shard_as_shard_order from input specs to output specs.

    When inputs carry _StridedShard with an explicit flag, all output (and input)
    DTensorSpecs in the strategy that also contain _StridedShard must agree.
    Strategy functions may forget to propagate the flag; this function fixes
    them up centrally after the strategy is produced.
    """
    _use_strided: bool | None = None
    for spec in op_schema.args_spec:
        if any(isinstance(p, _StridedShard) for p in spec.placements):
            val = spec.use_strided_shard_as_shard_order
            if _use_strided is not None and _use_strided != val:
                raise ValueError(
                    "Conflicting use_strided_shard_as_shard_order across "
                    f"input specs: got both {_use_strided} and {val}"
                )
            _use_strided = val

    if _use_strided is None:
        return

    def _fixup(spec: DTensorSpec) -> None:
        if not any(isinstance(p, _StridedShard) for p in spec.placements):
            return
        if spec.use_strided_shard_as_shard_order == _use_strided:
            return
        spec.use_strided_shard_as_shard_order = _use_strided
        if _use_strided:
            spec.shard_order = None  # pyrefly: ignore[bad-assignment]
        else:
            spec.shard_order = DTensorSpec.compute_default_shard_order(spec.placements)

    for op_spec in op_strategy.strategies:
        out = op_spec.output_specs
        if out is not None:
            if isinstance(out, DTensorSpec):
                _fixup(out)
            else:
                for s in out:
                    if s is not None:
                        _fixup(s)
        if op_spec.input_specs is not None:
            for s in op_spec.input_specs:
                _fixup(s)
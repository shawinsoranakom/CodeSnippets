def _select_min_cost_strategy(
    strategy: OpStrategy, op_schema: OpSchema | None = None
) -> OpSpec:
    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if len(strategy.strategies) == 1:
        # short cut with only one possible OpSpec
        return strategy.strategies[0]

    op_spec_costs: list[torch.types.FloatLikeType] = []
    no_redistribute_strategy_index: int = -1
    negative_cost_index: int = -1
    zero_cost_index: int = -1
    for strategy_idx, op_spec in enumerate(strategy.strategies):
        if op_spec.redistribute_cost is None:
            raise AssertionError("must set redistribute cost each OpSpec!")
        redistribute_cost = sum(chain.from_iterable(op_spec.redistribute_cost))
        op_spec_costs.append(redistribute_cost)

        # If there are strategies with negative/zero/no redistribute cost,
        # we record those indices.
        # TODO: Currently this only applies to OpStrategy selection. Requires extra
        # logic to make it work for TupleStrategy, if needed.
        if op_schema is not None:
            if guard_or_false(redistribute_cost < 0):
                if (
                    negative_cost_index == -1
                    or redistribute_cost < op_spec_costs[negative_cost_index]
                ):
                    negative_cost_index = strategy_idx
            elif guard_or_false(redistribute_cost == 0):
                needs_redistribute = False
                for spec_idx, input_spec in enumerate(op_schema.args_spec):
                    desired_spec = (
                        op_spec.output_spec
                        if op_spec.input_specs is None
                        else op_spec.input_specs[spec_idx]
                    )
                    if input_spec.placements != desired_spec.placements:
                        needs_redistribute = True
                        break

                if not needs_redistribute:
                    no_redistribute_strategy_index = strategy_idx
                elif zero_cost_index == -1:
                    zero_cost_index = strategy_idx

    # prioritize negative/zero/no redistribute cost strategies
    if negative_cost_index != -1:
        # If there's negative cost, we select the one with the minimal cost,
        # even if this means we need to redistribute, e.g. via local chunking.
        # E.g. this can happen for ops in self.op_to_shape_and_stride_idx
        # when the inputs / outputs are sharded.
        selected_strategy_index = negative_cost_index
    elif no_redistribute_strategy_index != -1:
        selected_strategy_index = no_redistribute_strategy_index
    elif zero_cost_index != -1:
        selected_strategy_index = zero_cost_index
    else:
        # default to choosing minimal redistribute cost
        selected_strategy_index = _select_min_redistribute_cost(
            op_spec_costs, strategy.strategies, op_schema
        )

    return strategy.strategies[selected_strategy_index]
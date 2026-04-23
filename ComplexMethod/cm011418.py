def spec_to_strategy(spec: object) -> object:
            if isinstance(spec, DTensorSpec):
                return OpStrategy([OpSpec(spec)])
            elif isinstance(spec, (list, tuple)) and len(spec) > 0:
                if all(isinstance(s, DTensorSpec) for s in spec):
                    # tensor list create tuple strategy
                    tuple_strategy = [spec_to_strategy(s) for s in spec]
                    tuple_strategy = cast(Sequence[StrategyType], tuple_strategy)
                    return TupleStrategy(
                        tuple(tuple_strategy)
                        if isinstance(spec, tuple)
                        else tuple_strategy
                    )
                elif any(isinstance(s, DTensorSpec) for s in spec):
                    # mixed list (e.g. [DTensorSpec, None, DTensorSpec]) for
                    # ops like aten.index.Tensor; keep as list so pytree
                    # flattening can extract OpStrategy items
                    return [spec_to_strategy(s) for s in spec]
                else:
                    return spec
            else:
                return spec
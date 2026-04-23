def sizes_strides_user(
        sizes: list[object], strides: list[object]
    ) -> SymInt | SymFloat | SymBool | int | float | bool:
        import sympy

        from torch.fx.experimental.symbolic_shapes import (
            eval_is_non_overlapping_and_dense,
        )

        for a in itertools.chain(sizes, strides):
            if isinstance(a, SymInt):
                return wrap_node(
                    getattr(a.node, method)(
                        [to_node(a.node, b) for b in sizes],
                        [to_node(a.node, b) for b in strides],
                    )
                )
        if method == "is_non_overlapping_and_dense_indicator":
            return eval_is_non_overlapping_and_dense(
                sizes,  # pyrefly: ignore[bad-argument-type]
                strides,  # pyrefly: ignore[bad-argument-type]
            )
        else:
            # TODO: this is an awful implementation
            return bool(
                func(
                    [sympy.sympify(a) for a in sizes],
                    [sympy.sympify(a) for a in strides],
                )
            )
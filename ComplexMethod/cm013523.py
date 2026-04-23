def _produce_dyn_sizes_from_int_tuple(
        self,
        tensor_size: Sequence[IntLikeType],
        source: Source,
        symbolic_context: SymbolicContext,
        hint_overrides: dict[int, int] | None = None,
    ) -> list[sympy.Expr]:
        if not all(not is_symbolic(val) for val in tensor_size):
            raise AssertionError(
                f"Expect size to be a plain tuple of ints but got {tensor_size}"
            )
        from torch._dynamo.source import TensorProperty, TensorPropertySource

        if not hint_overrides:
            hint_overrides = {}

        _assert_symbol_context(symbolic_context)
        dynamic_dims = symbolic_context.dynamic_sizes  # type: ignore[attr-defined]
        constraint_dims = symbolic_context.constraint_sizes  # type: ignore[attr-defined]
        size = []
        for i, val in enumerate(tensor_size):
            sym = self.create_symbol(
                hint_overrides.get(i, val),
                TensorPropertySource(source, TensorProperty.SIZE, i),
                dynamic_dims[i],
                constraint_dims[i],
                do_not_specialize_zero_one=config.backed_size_oblivious,
                symbolic_context=symbolic_context,
            )
            if (
                isinstance(symbolic_context, StatelessSymbolicContext)
                and symbolic_context.specialize_on
            ):
                for specialization in symbolic_context.specialize_on[i]:
                    self.specializations.add(
                        Specialization(
                            TensorPropertySource(source, TensorProperty.SIZE, i),
                            specialization,
                        )
                    )
            if (
                config.backed_size_oblivious
                and isinstance(sym, sympy.Symbol)  # could be static
                and symbol_is_type(sym, SymT.SIZE)
            ):
                self.size_like.add(sym)
            size.append(sym)
        return size
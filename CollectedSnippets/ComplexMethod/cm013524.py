def _create_symbolic_sizes_strides_storage_offset(
        self,
        # NB: SymInt is allowed here due to nested int, normally you don't
        # actually pass true symbolic sizes to this function
        ex_size: Sequence[IntLikeType],
        ex_stride: Sequence[IntLikeType],
        ex_storage_offset: IntLikeType,
        is_dim_dynamic: Sequence[bool],
        source: Source,
        *,
        symbolic_context: SymbolicContext | None = None,
        hint_overrides: dict[int, int] | None = None,
    ) -> tuple[
        tuple[IntLikeType, ...],
        tuple[IntLikeType, ...],
        IntLikeType,
    ]:
        dim = len(ex_size)

        if not hint_overrides:
            hint_overrides = {}

        # Reimplement the legacy behavior
        if symbolic_context is None:
            constraint_sizes: list[DimConstraint] = [None] * dim
            constraint_strides: list[DimConstraint] = [None] * dim
            dynamic_dims = []
            dynamic_strides = []
            for i in range(dim):
                # NB: This is encapsulation breaking!  Legacy behavior was
                # bad.
                if is_dim_dynamic[i]:
                    r = DimDynamic.DYNAMIC
                elif self.assume_static_by_default:
                    r = DimDynamic.STATIC
                else:
                    r = DimDynamic.DUCK
                dynamic_dims.append(r)
                dynamic_strides.append(r)
            dynamic_dims = [DimDynamic.DUCK] * dim
            dynamic_strides = [DimDynamic.INFER_STRIDE] * dim
            # symbolic_context is None - set one
            symbolic_context = StatelessSymbolicContext(
                dynamic_sizes=dynamic_dims,
                dynamic_strides=dynamic_strides,
                constraint_sizes=constraint_sizes,
                constraint_strides=constraint_strides,
            )
        # We got a StatelessSymbolicContext
        _assert_symbol_context(symbolic_context)
        constraint_sizes = symbolic_context.constraint_sizes  # type: ignore[attr-defined]
        constraint_strides = symbolic_context.constraint_strides  # type: ignore[attr-defined]
        dynamic_sizes = symbolic_context.dynamic_sizes  # type: ignore[attr-defined]
        dynamic_strides = symbolic_context.dynamic_strides  # type: ignore[attr-defined]

        # TODO: make this configurable from outside symbolic_context; we made a symbolic_context
        # decision here where if all sizes are static, we are going to
        # specialize all of the inner strides/offset too. We don't have to
        # do this, and arguably we should ALWAYS allow for dynamic offset,
        # this is cheap.
        # TODO: This should be DYNAMIC, using DUCK for BC
        dynamic_offset = (
            DimDynamic.STATIC
            if all(r == DimDynamic.STATIC for r in dynamic_sizes)
            else DimDynamic.DUCK
        )
        are_sizes_static = all(r == DimDynamic.STATIC for r in dynamic_sizes)

        if len(dynamic_sizes) != dim:
            raise AssertionError(f"{len(dynamic_sizes)} != {dim}")
        if len(dynamic_strides) != dim:
            raise AssertionError(f"{len(dynamic_strides)} != {dim}")
        if len(constraint_sizes) != dim:
            raise AssertionError(f"len(constraint_sizes) != {dim}")
        if len(constraint_strides) != dim:
            raise AssertionError(f"len(constraint_strides) != {dim}")

        from torch._dynamo.source import TensorProperty, TensorPropertySource

        size: list[sympy.Expr] = self._produce_dyn_sizes_from_int_tuple(
            ex_size, source, symbolic_context, hint_overrides=hint_overrides
        )
        # Record tensor exclusion constraints for stable graph selection.
        # The ndim check guards against stale excluded_sizes from graph
        # breaks where the resumed tensor may have different dimensionality.
        # Skip dims with hint overrides: the overridden hint in
        # backed_var_to_val would mismatch the excluded value, causing the
        # not-all check in produce_guards_verbose to emit a guard that
        # immediately fails.
        excluded_sizes = getattr(symbolic_context, "excluded_sizes", None)
        if (
            excluded_sizes
            and len(excluded_sizes) == dim
            and any(v is not None for v in excluded_sizes)
        ):
            for i in range(dim):
                ev = excluded_sizes[i]
                if (
                    ev is not None
                    and isinstance(size[i], sympy.Symbol)
                    and i not in (hint_overrides or {})
                ):
                    self._record_exclusion_constraint(size[i], ev)
        stride = self._compute_symbolic_stride(
            source,
            size,
            ex_size,
            ex_stride,
            dynamic_strides,
            constraint_strides,
            are_sizes_static,
            symbolic_context,
        )

        sym_sizes = [
            self.create_symintnode(
                sym,
                hint=hint_overrides.get(i, hint),
                source=TensorPropertySource(source, TensorProperty.SIZE, i),
            )
            for i, (sym, hint) in enumerate(zip(size, ex_size))
        ]

        for i, sym in enumerate(sym_sizes):
            if isinstance(sym, torch.SymInt) and i in hint_overrides:
                self.var_to_hint_override[sym.node.expr] = hint_overrides[i]

        sym_stride = []
        for i, stride_expr in enumerate(stride):
            # NB: Don't duck size the stride; instead use the expression
            # we computed
            if stride_expr is None:
                raise AssertionError(f"stride_expr is None for index {i}")
            # self.backed_var_to_val will have the up to date hint value for each symbols
            # including overridden hints.
            hint_stride = stride_expr.xreplace(self.backed_var_to_val)
            if isinstance(hint_stride, (int, sympy.core.numbers.Integer)):
                hint_stride = int(hint_stride)
            else:
                hint_stride = ex_stride[i]
            sym_stride.append(
                self.create_symintnode(
                    stride_expr,
                    hint=hint_stride,
                    source=TensorPropertySource(source, TensorProperty.STRIDE, i),
                )
            )
        sym_storage_offset = self.create_symintnode(
            self.create_symbol(
                ex_storage_offset,
                TensorPropertySource(source, TensorProperty.STORAGE_OFFSET),
                dynamic_dim=dynamic_offset,
                constraint_dim=None,
                symbolic_context=symbolic_context,
            ),
            hint=ex_storage_offset,
            source=TensorPropertySource(source, TensorProperty.STORAGE_OFFSET),
        )
        return tuple(sym_sizes), tuple(sym_stride), sym_storage_offset
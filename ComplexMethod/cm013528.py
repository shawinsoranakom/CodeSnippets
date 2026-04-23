def create_symbol(
        self,
        val: IntLikeType | FloatLikeType,
        source: Source,
        dynamic_dim: DimDynamic = DimDynamic.DUCK,
        constraint_dim: DimConstraint = None,  # NB: includes None
        positive: bool | None = True,
        do_not_specialize_zero_one: bool = False,
        symbolic_context: SymbolicContext | None = None,
    ) -> sympy.Expr:
        """Create a new symbol which is tracked by this ShapeEnv"""
        # check if constraint_dim is actually static integer
        if (
            isinstance(constraint_dim, StrictMinMaxConstraint)
            and constraint_dim.vr.lower == constraint_dim.vr.upper
        ):
            dynamic_dim = DimDynamic.STATIC
            if constraint_dim.vr.lower != val:
                raise ConstraintViolationError(
                    f"Static shape constraint of {constraint_dim.vr.lower} does not match input size of {val}, "
                    f"for {source.name}"
                )
            if isinstance(symbolic_context, StatelessSymbolicContext):
                from torch._dynamo.source import TensorPropertySource

                if not isinstance(source, TensorPropertySource):
                    raise AssertionError(
                        f"Expected TensorPropertySource, got {type(source)}"
                    )
                # TODO: storage_offset handling?
                if source.idx is None:
                    raise AssertionError("source.idx must not be None")
                symbolic_context.dynamic_sizes[source.idx] = dynamic_dim
                symbolic_context.constraint_sizes[source.idx] = None
            constraint_dim = None

        # see note [Tensor Fakification and Symbol Caching]
        source_name = source.name
        if (
            isinstance(symbolic_context, StatefulSymbolicContext)
            and id(self) not in symbolic_context.shape_env_to_source_to_symbol_cache
        ):
            symbolic_context.shape_env_to_source_to_symbol_cache[id(self)] = {}

        if (
            isinstance(symbolic_context, StatefulSymbolicContext)
            and source_name
            and (
                source_name
                in symbolic_context.shape_env_to_source_to_symbol_cache[id(self)]
            )
        ):
            return symbolic_context.shape_env_to_source_to_symbol_cache[id(self)][
                source_name
            ]

        if dynamic_dim is DimDynamic.UNBACKED:
            # Check if this unbacked dimension has a shape_id.
            # If so, we allocate a fresh symbol but add a runtime equality check
            # via torch._check against the existing symbols with the same shape_id.
            shape_id = None
            unbacked_min = None
            unbacked_max = None
            if (
                isinstance(symbolic_context, StatelessSymbolicContext)
                and symbolic_context.shape_ids is not None
            ):
                from torch._dynamo.source import TensorPropertySource

                if isinstance(source, TensorPropertySource) and source.idx is not None:
                    shape_id = symbolic_context.shape_ids.get(source.idx)

            # Check for unbacked bounds
            if (
                isinstance(symbolic_context, StatelessSymbolicContext)
                and symbolic_context.unbacked_bounds is not None
            ):
                from torch._dynamo.source import TensorPropertySource

                if isinstance(source, TensorPropertySource) and source.idx is not None:
                    bounds = symbolic_context.unbacked_bounds.get(source.idx)
                    if bounds is not None:
                        unbacked_min, unbacked_max = bounds

            # Always allocate a fresh unbacked symbol
            out = self.create_unbacked_symint(source).node.expr
            self._constrain_range_for_size(out)

            # Apply min/max bounds via torch._check if specified
            if unbacked_min is not None or unbacked_max is not None:
                out_symint = self.create_symintnode(out, hint=None)
                if unbacked_min is not None:
                    torch._check(out_symint >= unbacked_min)
                if unbacked_max is not None:
                    torch._check(out_symint <= unbacked_max)

            # Add runtime equality check for shape_id if applicable
            if shape_id is not None:
                if shape_id in self._shape_id_to_unbacked_symbol:
                    # Add runtime equality check instead of reusing the same symbol
                    existing_sym = self._shape_id_to_unbacked_symbol[shape_id]
                    existing_symint = self.create_symintnode(existing_sym, hint=None)
                    out_symint = self.create_symintnode(out, hint=None)
                    torch._check(out_symint == existing_symint)
                else:
                    self._shape_id_to_unbacked_symbol[shape_id] = out

            self.unbacked_inputs.add(out)

            if isinstance(symbolic_context, StatefulSymbolicContext) and source_name:
                symbolic_context.shape_env_to_source_to_symbol_cache[id(self)][
                    source_name
                ] = out
            return out

        if do_not_specialize_zero_one:
            specialize_zero_one = False
        else:
            specialize_zero_one = self.specialize_zero_one

        if not isinstance(source, Source):
            raise AssertionError(f"{type(source)} {source}")
        if positive and val < 0:
            raise AssertionError(f"positive set for negative value: {val}")
        # It's always sound to allocate a symbol as DYNAMIC.  If the user
        # constrained the symbol, force the symbolic_context to DYNAMIC, because our
        # constraint code will do weird stuff if, e.g., it's duck shaped
        if constraint_dim is not None:
            dynamic_dim = DimDynamic.DYNAMIC

        if dynamic_dim is DimDynamic.STATIC:
            out = sympy.Integer(val)
            if isinstance(symbolic_context, StatefulSymbolicContext) and source_name:
                symbolic_context.shape_env_to_source_to_symbol_cache[id(self)][
                    source_name
                ] = out
            return out

        elif dynamic_dim is DimDynamic.DUCK:
            # duck_shape can be used to globally turn off duck shaping, even
            # if it was requested
            duck = self.duck_shape
        elif dynamic_dim is DimDynamic.DYNAMIC:
            duck = False
        else:
            raise AssertionError(f"unhandled dynamic_dim {dynamic_dim}")

        sloc = self._get_sloc()

        if val in (0, 1) and specialize_zero_one:
            if val == 0:
                return sympy.S.Zero
            else:
                return sympy.S.One
        elif not duck or val not in self.val_to_var:
            # If we're not duck shaping, we always create a new symbol
            # Even if we're duck shaping, if we haven't seen this particular
            # value before, we also create a new symbol
            symbol_id = self._generate_unique_id(source.name)
            if type(val) is int or is_nested_int(val):
                sympy_expr = make_symbol(
                    SymT.SIZE, symbol_id, positive=positive, integer=True
                )
            else:
                sympy_expr = make_symbol(
                    SymT.FLOAT, symbol_id, positive=positive, real=True
                )
            self.source_to_var[source_name] = sympy_expr
            # We always associate vars to vals
            if isinstance(val, int):
                self.backed_var_to_val[sympy_expr] = sympy.Integer(val)
            elif isinstance(val, float):
                self.backed_var_to_val[sympy_expr] = sympy.Float(val)
            else:
                # Only used for jagged layout nested tensors
                self.backed_var_to_val[sympy_expr] = SingletonInt(
                    val.node.nested_int(), coeff=val.node.nested_int_coeff()
                )

            # Do the appending later, because we always want to populate this
            self.var_to_sources[sympy_expr] = []
            # Create a Z3 variable for the new symbol.
            self._add_z3var(sympy_expr, int)

            if duck:
                # Make sure to reuse this symbol for subsequent duck shaping

                self.val_to_var[val] = sympy_expr

            if isinstance(val, int):
                if positive:
                    # Add assertions for the newly created symbols
                    self._add_assertion(sympy_expr > 1)

                    # Apply default range, which assumes not zero-one
                    self.var_to_range[sympy_expr] = self._default_value_range(
                        do_not_specialize_zero_one
                    )
                    self.var_to_range_sloc[sympy_expr] = ValueRangesSLoc(
                        self._get_sloc(
                            "user code shown is first use of this value--the guard itself is not "
                            "due user code but due to 0/1 specialization in the framework; to "
                            "avoid specialization try torch._dynamo.decorators.mark_unbacked(tensor, dim)"
                            if self.specialize_zero_one
                            else None
                        ),
                        sloc,
                    )
                else:
                    self.var_to_range[sympy_expr] = (
                        self._default_unspecified_value_range()
                    )
                    self.var_to_range_sloc[sympy_expr] = ValueRangesSLoc(sloc, sloc)

                # Small performance optimization: if we have a min-max constraint,
                # we can proactively narrow to that range
                if isinstance(constraint_dim, StrictMinMaxConstraint):
                    if duck:
                        raise AssertionError(
                            "duck must be False for StrictMinMaxConstraint"
                        )
                    self._update_var_to_range(
                        sympy_expr, constraint_dim.vr, is_constraint=True
                    )

                vr = self.var_to_range[sympy_expr]
                if not vr.is_int:
                    raise AssertionError("vr must be int")

                if val not in vr:
                    raise ConstraintViolationError(
                        f"{val} not in range [{vr.lower}, {vr.upper}]"
                    )

                range_str = f"[{vr.lower}, {vr.upper}]"
            elif isinstance(val, float):
                self.var_to_range[sympy_expr] = vr = ValueRanges(-sympy.oo, sympy.oo)
                self.var_to_range_sloc[sympy_expr] = ValueRangesSLoc(sloc, sloc)
                range_str = f"[{vr.lower}, {vr.upper}]"
                if not vr.is_float:
                    raise AssertionError("vr must be float")
            else:
                # Skip var_range logic for SingletonInt
                # Only used for jagged layout nested tensors
                range_str = ""

            r = sympy_expr

            is_debug = config.extended_debug_create_symbol is not None and str(
                sympy_expr
            ) in config.extended_debug_create_symbol.split(",")
            maybe_more_info = ""
            if not is_debug and os.getenv("TORCHDYNAMO_EXTENDED_ADVICE", "1") not in (
                "0",
                "",
            ):
                maybe_more_info = (
                    ", for more info run with "
                    f'TORCHDYNAMO_EXTENDED_DEBUG_CREATE_SYMBOL="{sympy_expr}" '
                    "or to suppress this message run with "
                    'TORCHDYNAMO_EXTENDED_ADVICE="0"'
                )
            sloc, maybe_extra_debug = self._get_stack_summary(is_debug)
            self.log.info(
                "create_symbol %s = %s for %s %s %s%s%s",
                sympy_expr,
                val,
                source.name,
                range_str,
                sloc,
                maybe_more_info,
                maybe_extra_debug,
                stack_info=is_debug,
            )
            trace_structured(
                "create_symbol",
                metadata_fn=lambda: {
                    "symbol": str(sympy_expr),
                    "val": repr(val),
                    "vr": range_str,
                    "source": source.name,
                    "user_stack": structured.from_traceback(
                        TracingContext.extract_stack()
                    ),
                    "stack": structured.from_traceback(
                        CapturedTraceback.extract(skip=1).summary()
                    ),
                },
            )

            self.counter["create_symbol"] += 1
        else:
            # This implements duck-shaping: input sizes that match are assigned
            # the same symint
            r = self.val_to_var[val]
            self.source_to_var[source_name] = r
            self.log.debug("create_symbol %s duck sized %s", r, source.name)

        if isinstance(r, sympy.Symbol):
            r_sources = self.var_to_sources[r]
            r_sources.append(source)
            if not source.is_ephemeral() and r_sources[0].is_ephemeral():
                # prefer non-ephemeral source first since it may be guarded on later
                r_sources[0], r_sources[-1] = r_sources[-1], r_sources[0]

            # This ensures we get zeros in symbol_guard_counts, which makes
            # some queries simpler (since we will accumulate mass on 0 this
            # way)
            self.symbol_guard_counter[r] = 0

        if isinstance(symbolic_context, StatefulSymbolicContext) and source_name:
            symbolic_context.shape_env_to_source_to_symbol_cache[id(self)][
                source_name
            ] = r
        return r
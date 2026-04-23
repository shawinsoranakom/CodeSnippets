def wrap_symint(
        self,
        value: int,
        dynamism: DimDynamic | None = None,
        context: SymIntSymbolicContext | None = None,
    ) -> VariableTracker:
        assert type(value) is int

        if self.name in self.tx.output.unspec_variable_map:
            return self.tx.output.unspec_variable_map[self.name]

        shape_env = self.tx.output.shape_env
        frame_state_entry: FrameStateSizeEntry | None = None
        if TracingContext.get().force_unspec_int_unbacked_size_like:
            wrapped_value = shape_env.create_unbacked_symint()
            _constrain_range_for_size(wrapped_value)
            self.tx.output.tracked_fakes.append(
                TrackedFake(wrapped_value, self.source, None)
            )

        # NB: We do not do float.  For motivation, see
        # https://docs.google.com/document/d/1INSCdYu1PxXcr43HrD82OudeEuS-qxQe1yZmLg2wy6A/edit
        # but the general idea is that we generate kernels that can
        # take unspecialized floats and use them in sizevar computation
        elif not is_constant_source(self.get_source()):
            if dynamism is None and torch._dynamo.config.specialize_int:
                # If specialize_int is False, also return
                # a constant (but this should have been handled
                # in the caller, TBH). But if `dynamism` is set, then actually
                # turn it into a symint
                self.install_guards(GuardBuilder.CONSTANT_MATCH)
                return ConstantVariable.create(value=value, source=self.source)

            name = self.source.name

            frame_state_entry = process_automatic_dynamic(
                self.tx,
                name,
                FrameStateSizeEntry.make_scalar(value),
                is_unspecialized_nn_module=self.source.guard_source.is_unspecialized_nn_module(),
            )

            # TODO: This should be dynamic, as we in general do not
            # know if bare integers are actually going to be sizevars
            # and it is inappropriate to eagerly duck size them with
            # real sizevars
            normalized_source_name = normalize_source_name(self.source.name)
            base_source = self.source
            if isinstance(base_source, ChainedSource):
                base_source = base_source.get_base()

            if dynamism is not None:
                dynamic_dim = dynamism
            elif (
                config.automatic_dynamic_shapes
                and frame_state_entry.scalar is auto_dynamic
            ):
                set_feature_use("dynamo.automatic_dynamic_shapes", True)
                dynamic_dim = get_automatic_dynamic_shapes_mark_as()
            elif (
                isinstance(base_source, LocalSource)
                and base_source.dynamism is not None
                # pyrefly: ignore[no-matching-overload]
                and dict(base_source.dynamism).get(normalized_source_name, {0: False})[
                    0
                ]
            ) or not config.assume_static_by_default:
                dynamic_dim = DimDynamic.DYNAMIC
            else:  # assume_static_by_default
                # TODO: dynamic_dim = DimDynamic.STATIC should work but
                # for some reason it doesn't
                if frame_state_entry.scalar is auto_dynamic:
                    set_feature_use("dynamo.automatic_dynamic_shapes", False)
                self.install_guards(GuardBuilder.CONSTANT_MATCH)
                return ConstantVariable.create(value=value)

            excluded_scalar = (
                frame_state_entry.excluded_scalar
                if config.automatic_dynamic_exclusion_guard
                and frame_state_entry is not None
                else None
            )
            wrapped_value = shape_env.create_unspecified_symint_and_symbol(
                value,
                source=self.source,
                dynamic_dim=dynamic_dim,
                excluded_value=excluded_scalar,
            )
            if not isinstance(wrapped_value, SymInt):
                raise AssertionError(f"Expected SymInt, got {type(wrapped_value)}")

            self.tx.output.tracked_fakes.append(
                TrackedFake(wrapped_value, self.source, context)
            )
        else:
            assert is_constant_source(self.get_source())
            # TODO: Do I actually need guard for constant source?
            self.install_guards(GuardBuilder.CONSTANT_MATCH)
            return ConstantVariable.create(value=value, source=self.source)

        assert not isinstance(self.get_source(), RandomValueSource)
        install_guard(self.get_source().make_guard(GuardBuilder.TYPE_MATCH))

        options = {"source": self.get_source()}

        proxy = self.tx.output.root_tracer.create_graph_input(
            re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
            type(wrapped_value),
            wrapped_value,
            source=self.get_source(),
        )

        sym_expr = wrapped_value.node.expr
        assert isinstance(sym_expr, sympy.Symbol), f"{sym_expr} is not a basic Symbol."
        self.tx.output.root_tracer.bound_symbols[sym_expr] = proxy
        unspec_var = SymNodeVariable.create(self.tx, proxy, wrapped_value, **options)
        # type: ignore[assignment]
        self.tx.output.unspec_variable_map[self.name] = unspec_var

        if not is_constant_source(self.get_source()):
            proxy.node.meta["grapharg"] = GraphArg(
                self.get_source(),
                wrapped_value,
                pass_arg_as_tensor=False,
                fake_tensor=None,
                is_tensor=False,
                example_strong_ref=wrapped_value,
            )

        return unspec_var
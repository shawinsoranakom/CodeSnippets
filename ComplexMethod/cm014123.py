def wrap_symfloat(self, value: float) -> VariableTracker:
        # SymFloat wrapping is special.  We first wrap it in the same way we
        # do an unspecialized primitive, and then we item() it into a
        # SymFloat.  Removal of the item() call is left to a later FX pass,
        # mostly because that pass is more easily done after we have lowered
        # to ATen ops.  (Dynamo doesn't do decomposition right now).

        if self.name in self.tx.output.unspec_variable_map:
            return self.tx.output.unspec_variable_map[self.name]

        frame_state_entry = process_automatic_dynamic(
            self.tx,
            self.source.name,
            # type: ignore[arg-type]
            FrameStateSizeEntry.make_scalar(value),
            is_unspecialized_nn_module=self.source.guard_source.is_unspecialized_nn_module(),
        )

        # NB: we specialize on nan input, because our guard modeling in
        # ShapeEnv cannot deal with nan
        if (
            torch._dynamo.config.specialize_float
            or is_constant_source(self.get_source())
            or math.isnan(value)
            or math.isinf(value)
            # We don't support cudagraphs for now. Without this cudagraphs
            # break because they expect all cuda inputs but our tensorified
            # float will be a f64[] cpu tensor. Fixes the following test
            # when specialize_float=False
            # python test/inductor/test_compiled_optimizers.py CompiledOptimizerTests.test_rmsprop_weight_decay_maximize_capturable_cuda
            or torch._inductor.config.triton.cudagraphs
            or justknobs_check("pytorch/compiler:unspecialize_float_killswitch", False)
            or (
                config.assume_static_by_default
                and frame_state_entry.scalar is not auto_dynamic
            )
        ):
            self.install_guards(GuardBuilder.CONSTANT_MATCH)
            return ConstantVariable.create(value=value, source=self.source)

        # NB: At the point we've gotten here, we don't assume static by
        # default.  Since we have a guard mechanism, there isn't really any
        # downside to trying to be dynamic for float all the time.  Unlike
        # ints, this won't make codegen perf worse.  Modest cost to compile
        # time.

        wrapped_value = torch.tensor(value, dtype=torch.float64)

        # We don't support specializing floats for grad checking tensors
        # See https://github.com/pytorch/pytorch/pull/140828 for more
        # context.
        if torch._C._functorch.is_gradtrackingtensor(wrapped_value):
            self.install_guards(GuardBuilder.CONSTANT_MATCH)
            return ConstantVariable.create(value=value, source=self.source)

        # TODO: Switch RandomValueSource over to use this, this is more
        # accurate
        assert not isinstance(self.get_source(), RandomValueSource)
        install_guard(self.get_source().make_guard(GuardBuilder.TYPE_MATCH))

        # The FloatTensorSource here is just for pedantic correctness: if you
        # guard against an UnspecializedPythonVariable, you need to guard
        # against the tensor-ified version of the local, otherwise it's not a
        # Tensor.  However, we never let the UnspecializedPythonVariable escape
        # here, so there should never actually be any guards against this
        # source.
        source = FloatTensorSource(self.get_source())
        options = {"source": source, "raw_value": value}

        # TODO: Maybe the tensor-ification should be built into the source,
        # rather than by special pattern match
        example_value = wrap_to_fake_tensor_and_record(
            wrapped_value, tx=self.tx, is_tensor=False, source=source
        )
        proxy = self.tx.output.root_tracer.create_graph_input(
            re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
            type(wrapped_value),
            example_value,
            source=source,
        )
        cache_real_value_when_export(self.tx, proxy, wrapped_value)

        unspec_var = wrap_fx_proxy_cls(
            UnspecializedPythonVariable,
            tx=self.tx,
            proxy=proxy,
            example_value=example_value,
            subclass_type=None,
            **options,
        )
        assert isinstance(unspec_var, UnspecializedPythonVariable)
        self.tx.output.unspec_variable_map[self.name] = unspec_var

        if self.tx.export and not isinstance(self.get_source(), LocalSource):
            raise AssertionError(
                f"Dynamo attempts to add additional input during export: value={wrapped_value}, source={self.get_source()}"
            )
        fake_tensor_value = None
        example_value = unspec_var.proxy.node.meta["example_value"]
        assert is_fake(example_value)

        fake_tensor_value = example_value
        # type: ignore[attr-defined]
        assert fake_tensor_value.fake_mode is self.tx.fake_mode, (
            f"fake mode ({fake_tensor_value.fake_mode}) from fake tensor metadata doesn't match mode"
            "({self.tx.fake_mode}) from InstructionTranslator"
        )

        # There's something a bit incoherent about pass_arg_as_tensor,
        # specifically regarding sources.
        #
        # Specifically, suppose we have "x: float" local argument.  We
        # eventually end up with an UnspecializedPythonVariable denoting
        # torch.as_tensor(x)... but it's source is still L['x'] (which if you
        # accessed it directly is a float!)  So you gotta be careful when
        # setting up your guards, because it's still going to be a float at
        # this point, the conversion happens only precisely at the point we're
        # actually calling the FX graph.  This happens to be what we want for
        # shape guard generation, but it's kind of unintuitive.
        proxy.node.meta["grapharg"] = GraphArg(
            self.get_source(),
            wrapped_value,
            pass_arg_as_tensor=True,
            # type: ignore[arg-type]
            fake_tensor=fake_tensor_value,
            is_tensor=False,
            example_strong_ref=wrapped_value,
        )

        # Directly do item to bypass capture_scalar_outputs
        r = wrap_fx_proxy(
            self.tx,
            self.tx.output.create_proxy(
                "call_method",
                "item",
                *proxy_args_kwargs([unspec_var], {}),
            ),
        )
        # type: ignore[attr-defined]
        self.tx.output.tracked_fakes.append(TrackedFake(r.sym_num, self.source, None))

        get_metrics_context().set("tensorify_float_attempt", True, overwrite=True)

        return r
def wrap_module(self, value: torch.nn.Module) -> VariableTracker:
        from ..eval_frame import OptimizedModule

        if len(value.__dict__) == 0:
            unimplemented(
                gb_type="Uninitialized nn.Module",
                context=typestr(value),
                explanation=f"Attempted to trace an uninitialized nn.Module of type {typestr(value)}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                    "Ensure your nn.Module instance has called `super().__init__()`.",
                ],
            )
        if istype(value, OptimizedModule):
            # Check if the optimized module was disabled
            if inspect.getattr_static(value.forward, "_torchdynamo_disable", False):
                # This bytecode is mostly of kind LOAD_ATTR or LOAD_METHOD. If
                # we graph break here, Dynamo does not know how to create
                # continuation functions for such bytecodes. So, we delay the
                # graph break to CALL_FUNCTION.
                msg = inspect.getattr_static(
                    value.forward, "_torchdynamo_disable_msg", None
                )
                return DelayGraphBreakVariable(
                    source=self.source,
                    msg=f"Optimized `nn.Module` is wrapped with `torch.compiler.disable` (reason: {msg})",
                )

            self.install_guards(GuardBuilder.TYPE_MATCH)
            self.source = AttrSource(self.source, "_orig_mod")
            return self.wrap_module(value._orig_mod)

        if type(value) is torch.jit._script.RecursiveScriptModule:
            unimplemented(
                gb_type="torch.jit.script/freeze modules unsupported",
                context=str(value),
                explanation="Dynamo does not support tracing into torch.jit.script or "
                "torch.jit.freeze modules because they execute in the TorchScript "
                "runtime, not Python. Replace the ScriptModule submodule with the "
                "original eager nn.Module.",
                hints=[
                    *graph_break_hints.FUNDAMENTAL,
                ],
            )

        if (
            isinstance(value, (torch.nn.RNN, torch.nn.GRU, torch.nn.LSTM))
            and not config.allow_rnn
        ):
            unimplemented(
                gb_type="Attempted to wrap RNN, GRU, or LSTM",
                context=str(value),
                explanation="Dynamo does not support RNN, GRU, or LSTM.",
                hints=[
                    "Set torch._dynamo.config.allow_rnn=True to enable experimental support for RNN, GRU, and LSTM in Dynamo",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        if getattr(value, "_is_fsdp_managed_module", False):
            # See note [Dynamo treats FSDP wrapped modules as UnspecializedNNModule]
            # in fully_sharded_data_parallel.py for more information

            # we can't do this assert inside FSDP constructor,
            # since we don't know yet whether dynamo will be used
            if not getattr(value, "_fsdp_use_orig_params", False):
                unimplemented(
                    gb_type="FSDP with use_orig_params=False",
                    context="",
                    explanation="Dynamo only supports FSDP with use_orig_params=True",
                    hints=[],
                )

            # Note on FSDP guarding
            # Eager FSDP already assumes (requires, but without enforcement)
            # that users don't mutate their model parameters/structure after
            # FSDP wrapping, because FSDP wouldn't notice or update its
            # FlatParams.
            #
            # Therefore, torch.compile can skip guarding on params or submodule
            # structure of fsdp_managed modules, by using FSDPNNModuleSource as
            # the guard source.  This behavior is gated on
            # config.skip_fsdp_guards.
            self.install_guards(GuardBuilder.TYPE_MATCH)
            result = FSDPManagedNNModuleVariable(value, source=self.get_source())
            if not SideEffects.cls_supports_mutation_side_effects(type(value)):
                # don't allow STORE_ATTR mutation with custom __setattr__
                return result
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif mutation_guard.is_dynamic_nn_module(value, self.tx.export):
            # created dynamically, don't specialize on it

            # Note [Tracing a torch.compiled function]
            # when make_fx tracing a compiled function, we need
            if isinstance(value, torch.fx.experimental.proxy_tensor._AttrProxy):
                # type: ignore[attr-defined]
                value = value.get_base()
                self.source = AttrProxySource(self.source)

            freezing = is_parameter_freezing()

            # Guard against the case where user may overwrite named parameters
            # / named buffers
            # NOTE: This is not likely to happen but worth guarding to avoid
            # exception
            if (
                callable(value.named_parameters)
                # type: ignore[attr-defined]
                and value.named_parameters.__func__ is og_module_named_parameters_fn_ptr
            ):
                try:  # catch TypeErrors in named_parameters() from unserializable nn modules
                    # type: ignore[attr-defined]
                    for _, p in value.named_parameters():
                        self.mark_static_input(p, guard=freezing)
                except TypeError as e:
                    raise_observed_exception(type(e), self.tx, args=list(e.args))

            if (
                callable(value.named_buffers)
                # type: ignore[attr-defined]
                and value.named_buffers.__func__ is og_module_named_buffers_fn_ptr
            ):
                try:  # catch TypeErrors in named_parameters() from unserializable nn modules
                    # type: ignore[attr-defined]
                    for _, b in value.named_buffers():
                        self.mark_static_input(b, guard=freezing)
                except TypeError as e:
                    raise_observed_exception(type(e), self.tx, args=list(e.args))

            if freezing:
                # we need to add the module to tracing context
                # in order to allow its params to get invalidated
                # this will get cleaned up once compile ends
                self.tx.output.nn_modules[self.name] = value

            if (
                value.__module__.startswith(("torch.nn.modules", "torch.ao."))
                and not value.__module__.startswith("torch.nn.modules.container")
            ) or getattr(value.__class__, "_dynamo_marked_static", False):
                new_source = self.source
                if not self.tx.output.export or config.install_free_tensors:
                    new_source = UnspecializedBuiltinNNModuleSource(self.source)
                result = UnspecializedBuiltinNNModuleVariable(value, source=new_source)
                install_guard(new_source.make_guard(GuardBuilder.TYPE_MATCH))
            else:
                new_source = self.source
                if not self.tx.output.export or config.install_free_tensors:
                    new_source = UnspecializedNNModuleSource(self.source)
                result = UnspecializedNNModuleVariable(value, source=new_source)
                install_guard(new_source.make_guard(GuardBuilder.TYPE_MATCH))

            self.tx.output.add_fqn_info_for_inlined_modules(value, self.source)

            if not SideEffects.cls_supports_mutation_side_effects(type(value)):
                # don't allow STORE_ATTR mutation with custom __setattr__
                return result
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif issubclass(
            value.__class__, torch.nn.parallel.distributed.DistributedDataParallel
        ):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return UnspecializedNNModuleVariable(value, source=self.get_source())
        else:
            return self.tx.output.register_attr_or_module(
                value,
                self.name,
                source=self.get_source(),
                # Guards are added inside register_attr_or_module
            )
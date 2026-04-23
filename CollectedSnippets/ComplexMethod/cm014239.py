def map_sources_and_install_guards(self, tx: "InstructionTranslator") -> None:
        from ..decorators import mark_static_address
        from .lazy import LazyVariableTracker

        self.grad_to_source = {}
        self.tensor_to_source = {}

        def mark_static(x: Any) -> None:
            mark_static_address(x, guard=True)

        tree_map_only(torch.Tensor, mark_static, self.value.state)

        # Recursively realize the variable trackers for optim.state and
        # optim.param_groups, which recursively install the necessary guards.
        params_groups_source = self.source and AttrSource(self.source, "param_groups")
        param_groups_vt = LazyVariableTracker.realize_all(
            VariableTracker.build(tx, self.value.param_groups, params_groups_source)
        )

        state_source = self.source and AttrSource(self.source, "state")
        state_vt = VariableTracker.build(tx, self.value.state, state_source)

        # We need to realize the top level state dict to populate
        # the guard locals
        state_vt.realize()
        assert state_source is not None
        tx.output.guard_on_key_order.add(state_source)

        # Populate self.grad_to_source and self.tensor_to_source so that we can
        # manually update_list_args
        for group, group_vt in zip(self.value.param_groups, param_groups_vt.items):
            # we assume here that all params within a param group
            # are initialized similarly
            if len(group["params"]) > 0:
                for param in group["params"]:
                    if param.grad is not None:
                        key_index = None
                        for i, k in enumerate(self.value.state.keys()):
                            if k is param:
                                key_index = i
                                break
                        if key_index:
                            LazyVariableTracker.realize_all(
                                VariableTracker.build(
                                    tx,
                                    self.value.state[param],
                                    DictGetItemSource(
                                        state_source,
                                        ConstDictKeySource(state_source, key_index),
                                    ),
                                )
                            )
                            break

            params_vt = group_vt.getitem_const(tx, ConstantVariable.create("params"))
            all_static = True
            non_static_grads = []
            for p, p_vt in zip(group["params"], params_vt.unpack_var_sequence(tx)):
                param_source = p_vt.source
                self.tensor_to_source[p] = param_source
                grad_source = GradSource(
                    param_source,
                    "grad",
                )

                if p.grad is not None:
                    self.grad_to_source[p.grad] = grad_source
                    if not _is_static_for_cudagraphs(p.grad):
                        all_static = False
                        non_static_grads.append(grad_source)
                else:
                    install_guard(grad_source.make_guard(GuardBuilder.CONSTANT_MATCH))

            # Note: to avoid spam logs only warn if perf hint artifact is enabled
            # (NB: artifacts are only enabled at the debug or warning level)
            if not all_static and perf_hint_log.isEnabledFor(logging.DEBUG):
                non_static_grad_names = [src.name for src in non_static_grads]
                perf_hint_log.warning(
                    (
                        "Grad tensors %s will be copied during cudagraphs execution."
                        "If using cudagraphs and the grad tensor addresses will be the same across runs,"
                        " use torch._dynamo.decorators.mark_static_address to elide this copy.",
                    ),
                    non_static_grad_names,
                )

        # We have to again iterate over the state dict to collect the
        # tensor_to_source dict. This is used for the finalizer.
        for idx, value in enumerate(self.value.state.values()):
            p_state_source = DictGetItemSource(
                state_source, ConstDictKeySource(state_source, idx)
            )
            tx.output.guard_on_key_order.add(p_state_source)
            for inner_idx, v in enumerate(value.values()):
                if (
                    isinstance(v, torch.Tensor)
                    and v not in self.grad_to_source
                    and v not in self.tensor_to_source
                ):
                    self.tensor_to_source[v] = DictGetItemSource(
                        p_state_source, ConstDictKeySource(p_state_source, inner_idx)
                    )
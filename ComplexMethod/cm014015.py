def register_attr_or_module(
        self,
        target: torch.nn.Module | torch.Tensor | Any,
        *names: Any,
        **options: Any,
    ) -> VariableTracker:
        if is_dynamic_nn_module(target, self.export):
            # Instead of returning UnspecializedNNModuleVariable, call
            # VariableTracker.build so that it is tracked for mutation.
            return VariableTracker.build(self.current_tx, target, **options)

        options = dict(options)
        assert "source" in options
        source = options["source"]
        assert not isinstance(source, ParamBufferSource)

        if isinstance(target, torch.Tensor):
            tracer = self.current_tracer
            if not self.is_root_tracer():
                # For higher order ops, we don't want to insert the get_attr in
                # innermost graph. Instead, we want to raise the params/buffers
                # as inputs to the higher-order graph, and register them as
                # get_attrs in the root tracer.

                # Note that Dynamo will still call lift_tracked_freevar_to_input
                # when these inputs are encountered for the inner graph. The
                # only difference is what happens at the root tracer for
                # nn.Parameters vs free inputs. The free inputs are registered
                # as placeholders in the root graph, whereas the nn.Parameters
                # are registered as get_attr nodes in the root graph.
                tracer = self.root_tracer

            def wrap_name(module_key: str) -> VariableTracker:
                assert self.param_name_to_source is not None
                self.param_name_to_source[module_key] = source

                # Check if the attr has already been registered. This can happen
                # when two different sources point to the same tensor.
                assert self.root_tx is not None
                if target in self.root_tx.output.side_effects:
                    return self.root_tx.output.side_effects[target]

                if get_static_address_type(target) == "guarded" and not isinstance(
                    source, NumpyTensorSource
                ):
                    install_guard(source.make_guard(GuardBuilder.ID_MATCH))
                elif not is_constant_source(source):
                    install_guard(source.make_guard(GuardBuilder.TENSOR_MATCH))

                vt = wrap_fx_proxy(
                    self.root_tx,
                    tracer.create_proxy("get_attr", module_key, (), {}),
                    example_value=target,
                    **options,
                )

                # Track the object so to avoid duplicate registration in case of
                # different sources pointing to the same tensor object.
                vt = self.root_tx.output.side_effects.track_object_existing(target, vt)

                assert "tensor_dict" not in vt.as_proxy().node.meta
                # pyrefly: ignore [bad-argument-type]
                vt.as_proxy().node.meta["tensor_dict"] = _extract_tensor_dict(target)

                return vt

        elif isinstance(target, torch.nn.Module):
            assert isinstance(target, torch.nn.Module)

            if source:
                install_guard(source.make_guard(GuardBuilder.NN_MODULE))

                def wrap_name(module_key: str) -> VariableTracker:
                    # pyrefly: ignore [bad-argument-type]
                    return NNModuleVariable(type(target), module_key, target, **options)

            else:
                # This is Dynamo created graph module, e.g., graph module coming
                # from higher order ops. NNModuleVariable tracker can't be
                # sourceless, so let's return a unspecializedNNModule variable
                # tracker.
                def wrap_name(module_key: str) -> VariableTracker:
                    # pyrefly: ignore[bad-argument-type]
                    return variables.UnspecializedNNModuleVariable(target, **options)

        elif isinstance(target, (torch.SymInt, torch.SymFloat)):
            # HACKY CODE REGION BEGIN
            # WE ARE PIGGYBACKING ON EXISTING INFRA TO REGISTER ATTRS
            # This ultimately gets written to self.nn_modules, which is unfortunate
            # Attrs that are tenors and symints and such need to be migrated to have their
            # own storage
            # alas, this is like this for now

            def wrap_name(module_key: str) -> VariableTracker:
                return SymNodeVariable.create(
                    self.root_tx,
                    self.create_proxy("get_attr", module_key, (), {}),
                    sym_num=target,
                    **options,
                )

            # HACKY CODE REGION END
        elif is_opaque_type(type(target)):
            # HACKY CODE REGION BEGIN
            # Same as SymInt/SymFloat above: piggybacking on self.nn_modules
            # to store opaque objects as graph attributes.

            tracer = self.current_tracer
            if not self.is_root_tracer():
                tracer = self.root_tracer

            def wrap_name(module_key: str) -> VariableTracker:
                fake_script_obj = torch._library.fake_class_registry.maybe_to_fake_obj(
                    self.fake_mode, target
                )
                proxy = tracer.create_proxy("get_attr", module_key, (), {})
                set_example_value(proxy.node, fake_script_obj)
                return torch._dynamo.variables.script_object.TorchScriptObjectVariable.create(
                    proxy, fake_script_obj, **options
                )

            # HACKY CODE REGION END

        else:

            def wrap_name(module_key: str) -> VariableTracker:
                self.output.update_co_names(module_key)
                self.global_scope[module_key] = target
                return VariableTracker.build(
                    self,  # type: ignore[arg-type]
                    target,
                    ConstantSource(source_name=module_key),
                )

        for k, v in self.nn_modules.items():
            if v is target:
                # it already exists
                return wrap_name(k)

        name = OutputGraph.module_key_name(*names)
        name = get_unique_name_wrt(name, self.nn_modules, self.global_scope)
        self.nn_modules[name] = target
        if isinstance(target, torch.nn.Module):

            def register_leaf_name(leaf_name: str) -> None:
                assert self.param_name_to_source is not None
                new_source = self.get_chained_param_buffer_source(source, leaf_name)
                new_name = f"{name}.{leaf_name}"
                self.param_name_to_source[new_name] = new_source
                if isinstance(source, LocalSource):
                    self.dynamo_flat_name_to_original_fqn[
                        OutputGraph.module_key_name(new_source.name)
                    ] = leaf_name

            # annoying, but there are cases when we do not have parameters
            # see test_nn_moduledict_contains
            if hasattr(target, "_parameters"):
                for leaf_name, _ in target.named_parameters():
                    register_leaf_name(leaf_name)
            if hasattr(target, "_buffers"):
                for leaf_name, _ in target.named_buffers():
                    register_leaf_name(leaf_name)

        return wrap_name(name)
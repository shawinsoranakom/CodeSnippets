def wrap_tensor(self, value: torch.Tensor) -> VariableTracker:
        source = self.get_source()

        # We cannot already be tracking the tensor, which implies
        # it would have already been wrapped
        assert value not in self.tx.output.side_effects

        is_static_input = get_static_address_type(value) is not None

        if not is_static_input and (
            isinstance(value, torch.nn.Parameter)
            # mark tensor attributes of nn modules static
            or (source and source.guard_source.is_unspecialized_nn_module())
        ):
            self.mark_static_input(value, guard=is_parameter_freezing())
            is_static_input = True

        # Install any tensors which are "free" variables; that is:
        # 1. Globals
        # 2. NonLocals
        # 3. tensors that are attributes of nn module
        should_install_free_tensor = config.install_free_tensors and (
            is_from_global_source(source)
            or is_from_nonlocal_source(source)
            or is_from_unspecialized_nn_module_source(source)
        )

        make_graph_attribute = is_static_input and (
            is_parameter_freezing() or torch._dynamo.config.prepare_freezing
        )

        if should_install_free_tensor or (
            (source.guard_source.is_specialized_nn_module() or make_graph_attribute)
            and not source.guard_source.is_fsdp_module()
        ):
            self.assert_not_wrapped_by_this_graph(value)
            return self.tx.output.register_attr_or_module(
                value, self.name, source=source
            )

        if get_static_address_type(value) == "guarded":
            # If it's a guarded tensor, we can install the parameter directly
            # into  the Fx graph instead of lifting it as an input. Lifting
            # offers no benefit,  such as regional compilation, since we still
            # guard on the tensor's ID.  Moreover, installing it in the Fx graph
            # eliminates the pre-graph bytecode  required to extract the tensor
            # from locals/globals, reducing overhead.  This can lead to
            # significant cost savings, especially for optimizers  handling many
            # tensors.
            self.install_guards(GuardBuilder.ID_MATCH)
            self.assert_not_wrapped_by_this_graph(value)
            return self.tx.output.register_attr_or_module(
                value, self.name, source=source
            )

        if is_constant_source(source):
            self.assert_not_wrapped_by_this_graph(value)
            return self.tx.output.register_attr_or_module(
                value,
                re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
                source=source,
                # Guards are added inside register_attr_or_module
            )

        # NB: this just says we accessed a tensor from the same source again
        # (e.g., a tensor lives in a global foo, and we LOAD_GLOBAL it twice).
        # This is distinct from two distinct sources mapping to the same
        # Tensor (per id())!  No guard is necessary here.  See below for the
        # other case.
        is_duplicate_tensor = source in self.tx.output.input_source_to_var
        if is_duplicate_tensor:
            return self.tx.output.input_source_to_var[source]

        options = {}
        subclass_type = infer_subclass_type(value)
        if subclass_type is not None:
            self.install_guards(GuardBuilder.TYPE_MATCH)

        if get_static_address_type(value) == "guarded":
            self.install_guards(GuardBuilder.ID_MATCH)

        # By this point, we should have deduplicated all tensors
        self.assert_not_wrapped_by_this_graph(value)

        if (
            isinstance(value, torch.Tensor)
            and value.is_nested
            and not isinstance(value, torch.nested._internal.nested_tensor.NestedTensor)
        ):
            unimplemented(
                gb_type="Attempted to wrap strided NestedTensor",
                context="",
                explanation="torch.compile does not support strided NestedTensor",
                hints=[],
            )

        # TODO(pearu,sparse-team) - Add the corresponding SPARSE_TENSOR_MATCH guards
        if (
            isinstance(value, torch.Tensor)
            and is_sparse_any(value)
            and (not self.tx.export or not config.capture_sparse_compute)
        ):
            # A hot fix for sparse tensors + torch.compile. Support for
            # export + sparsity is being added but we need to create
            # SPARSE_TENSOR_GUARDS for guards to work properly.
            unimplemented(
                gb_type="Attempted to wrap sparse Tensor",
                context="",
                explanation="torch.compile does not support sparse Tensors",
                hints=[*graph_break_hints.SPARSE_TENSOR],
            )

        if (
            safe_has_grad(value)
            and safe_grad(value) is not None
            # type: ignore[attr-defined]
            and value.dtype != safe_grad(value).dtype
        ):
            safe_grad_val = safe_grad(value)
            grad_str = str(safe_grad_val.dtype) if safe_grad_val is not None else "None"
            unimplemented(
                gb_type="dtype mismatch between tensor and its gradient",
                context=f"tensor dtype: {value.dtype}; grad dtype: {grad_str}",
                explanation="Inconsistent dtype between tensor and its gradient. "
                "This can happen in FSDP and crashes meta tensor creation.",
                hints=[*graph_break_hints.SUPPORTABLE],
            )

        # tx.output has multiple tracers if we're introspecting HigherOrderOperator.
        # When we've discovered an untracked tensor, then we actually need
        # to get Dynamo to track the tensor (which is what this function does)
        # and put it as a graph input on the root tracer. Later on,
        # if the input is actually used in the body of the HigherOrderOperator,
        # then the relevant SubgraphTracer will lift it to being an input of
        # the subgraph.
        # See NOTE [HigherOrderOperator tracing design] for more details.

        example_value = wrap_to_fake_tensor_and_record(
            value, tx=self.tx, is_tensor=True, source=source
        )

        tensor_proxy = self.tx.output.root_tracer.create_graph_input(
            re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
            type(value),
            example_value,
            source=source,
        )
        cache_real_value_when_export(self.tx, tensor_proxy, value)

        tensor_variable = wrap_fx_proxy(
            tx=self.tx,
            proxy=tensor_proxy,
            example_value=example_value,
            subclass_type=subclass_type,
            source=source,
            **options,
        )

        # Track input tensors for attribute mutation, matching how
        # handle_traced_output tracks intermediate tensors with AttributeMutationNew.
        # This enables setattr on input tensors (e.g. tensor.custom_attr = val)
        # without graph breaking.
        self.tx.output.side_effects.track_object_existing(value, tensor_variable)

        if value._is_view():
            # If value is a view, add its base tensor to the tracked fakes list.
            # This is so we are able to access the correct source for its symbolic
            # shape values, in case we need them.
            wrap_to_fake_tensor_and_record(
                value._base,
                tx=self.tx,
                source=AttrSource(source, "_base"),
                is_tensor=True,
            )

        guard_type = GuardBuilder.TENSOR_MATCH

        if isinstance(source, GradSource) and is_from_optimizer_source(source):
            guard_type = GuardBuilder.NOT_NONE_MATCH

        is_dtensor = torch.distributed.is_available() and isinstance(
            value, torch.distributed.tensor.DTensor
        )
        if not is_dtensor:
            # We guard on the _local_tensor and the _spec, and therefore we dont
            # have to guard on the outer DTensor.
            self.install_guards(
                functools.partial(
                    guard_type,
                    value=(
                        value
                        if isinstance(source, NumpyTensorSource)
                        else TensorWeakRef(value)
                    ),
                )
            )

        # We install TYPE_MATCH guards for traceable wrapper subclass object,
        # and recursively install corresponding guard for each inner attribute.
        if is_traceable_wrapper_subclass(value):
            # Tensor subclass guards are very expensive because they are
            # implemented in Python. Since DTensor is PyTorch-maintained class,
            # we can skip a lot of these guards.
            if is_dtensor:
                self.install_guards(GuardBuilder.TYPE_MATCH)

                inner_attrs = value.__tensor_flatten__()[0]
                if inner_attrs != ["_local_tensor", "device_mesh"]:
                    raise RuntimeError(
                        "Expecting DTensor inner attrs to be ['_local_tensor', 'device_mesh']"
                    )

                flattening_ctx = value.__tensor_flatten__()[1]
                if not (
                    len(flattening_ctx) == 4
                    and flattening_ctx[0] == value._spec.placements
                    and flattening_ctx[1] == value._spec.tensor_meta
                    and flattening_ctx[2] == value._spec.shard_order
                    and flattening_ctx[3] == value.requires_grad
                ):
                    raise RuntimeError(
                        "Expecting DTensor flattening ctx to be (placements, tensor_meta, shard_order, requires_grad)"
                    )
                # Guard on the dtensor spec
                install_guard(
                    AttrSource(self.source, "_spec").make_guard(
                        GuardBuilder.DTENSOR_SPEC_MATCH
                    )
                )
                # Move this to C++
                install_guard(
                    AttrSource(self.source, "requires_grad").make_guard(
                        GuardBuilder.EQUALS_MATCH
                    )
                )
            else:
                self.install_guards(GuardBuilder.TENSOR_SUBCLASS_METADATA_MATCH)
                self.install_guards(GuardBuilder.TYPE_MATCH)
                install_guard(
                    SubclassAttrListSource(source).make_guard(GuardBuilder.EQUALS_MATCH)
                )

            attrs, _ = value.__tensor_flatten__()
            for attr in attrs:
                inner_value = getattr(value, attr)
                # FakeScriptObject wraps the real opaque object during
                # fake-mode tracing; unwrap before the type check.
                inner_type = type(inner_value)
                if isinstance(
                    inner_value,
                    torch._library.fake_class_registry.FakeScriptObject,
                ):
                    inner_type = type(inner_value.real_obj)
                if not isinstance(
                    inner_value, torch.Tensor
                ) and not is_opaque_reference_type(inner_type):
                    raise RuntimeError(
                        f"{type(inner_value).__name__!r} found in tensor attrs of "
                        f"{type(value).__name__}.__tensor_flatten__(). "
                        "Only tensors and reference-type opaques are allowed "
                        "in tensor attrs."
                    )
                inner_source = AttrSource(self.source, attr)
                LazyVariableTracker.realize_all(
                    VariableBuilder(self.tx, inner_source)(inner_value)
                )

        self.tx.output.input_source_to_var[source] = tensor_variable
        assert "tensor_dict" not in tensor_proxy.node.meta
        tensor_proxy.node.meta["tensor_dict"] = _extract_tensor_dict(value)

        # Note: this information is conveyed via subclass_type now
        # type: ignore[attr-defined]
        fake_tensor_value = tensor_variable.proxy.node.meta["example_value"]
        if maybe_get_fake_mode(fake_tensor_value) is not self.tx.fake_mode:
            raise InternalTorchDynamoError("Wrapped Tensor must be this graph's fake")

        grapharg = GraphArg(source, value, False, fake_tensor_value)
        tensor_proxy.node.meta["grapharg"] = grapharg
        return tensor_variable
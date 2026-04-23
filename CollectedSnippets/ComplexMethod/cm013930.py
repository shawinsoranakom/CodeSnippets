def TENSOR_MATCH(self, guard: Guard, value: Any | None = None) -> None:
        if config._unsafe_skip_fsdp_module_guards and guard.is_fsdp_module():
            return
        # For tensors that are part of the Dynamo extracted Fx graph module, an
        # ID_MATCH suffices.
        if match_on_id_for_tensor(guard):
            self.ID_MATCH(guard)
        else:
            if isinstance(value, TensorWeakRef):
                value = value()

            value = value if value is not None else self.get(guard)

            pytype = type(value)
            dispatch_keys = torch._C._dispatch_keys(value)
            if isinstance(value, torch._subclasses.FakeTensor):
                if value.pytype is not None:
                    pytype = value.pytype
                if value.dispatch_keys is not None:
                    dispatch_keys = value.dispatch_keys

            assert isinstance(value, torch.Tensor)

            if config.log_compilation_metrics and isinstance(value, torch.nn.Parameter):
                metrics_context = get_metrics_context()
                if metrics_context.in_progress():
                    metrics_context.increment("param_numel", value.numel())
                    metrics_context.increment("param_bytes", value.nbytes)
                    metrics_context.increment("param_count", 1)

            tensor_name = self.arg_ref(guard)
            # [Note - On Export Tensor Guards]
            #
            # In eager mode, tensor guards are evaluated through C++, in guards.cpp
            # see [Note - On Eager Tensor Guards] for more info.
            #
            # In export mode, we instead maintain parallel logic between C++ and python
            # here, with an exception of checking the dispatch key - with the idea that a dispatch key
            # is an entirely runtime notion that would make no sense to keep in an exported graph.
            #
            # Now, this idea is okay, but to paraphrase @ezyang, this mental model is sufficient for now, although
            # not entirely true.
            # For example, suppose one of the input tensors had the negative dispatch key.
            # You should end up with a graph that is specialized for tensors that have a negative dispatch key.
            # If you allow a Tensor that does NOT have this bit set, you will accidentally run it "as if" it were negated.
            # Now, negative key only shows up for complex numbers, and most likely, the exported to target doesn't
            # support this feature at all, but the point stands that :some: tensor state only shows up on dispatch key.
            # TODO(voz): Either populate a dispatch_key check into the guards, or error on users passing in an unsupported
            # subset of keys during export.
            #
            # The list of tensor fields and calls we care about can be found in `terms` below.
            # TODO(voz): We are missing storage offset in all our tensor guards?
            code: list[str] = []
            assert self.check_fn_manager.output_graph is not None
            if self.check_fn_manager.output_graph.export:
                self.TYPE_MATCH(guard)
                terms = [
                    "dtype",
                    "device",
                    "requires_grad",
                    "ndimension",
                ]

                for term in terms:
                    term_src = AttrSource(guard.originating_source, term)
                    if term == "ndimension":
                        term = "ndimension()"
                        term_src = CallFunctionNoArgsSource(term_src)
                    real_value = self.get(term_src)
                    if istype(real_value, (torch.device, torch.dtype)):
                        # copy pasted from EQUALS_MATCH
                        code.append(f"str({tensor_name}.{term}) == {str(real_value)!r}")
                    else:
                        code.append(f"{tensor_name}.{term} == {real_value}")
            else:
                guard_manager = self.get_guard_manager(guard)

                # skip_no_tensor_aliasing_guards_on_parameters bring
                # unsoundness. If you compile a function with two different
                # parameters, but later on you pass on same tensor as two
                # different outputs (aliasing), Dynamo will not detect this.
                # But we deliberately take this soundness hit because this
                # usecase is quite rare and there is substantial reduction in
                # guard overhead.
                # For numpy tensors, since those are ephemeral, we don't have to
                # insert aliasing guards on them
                if not (
                    config.skip_no_tensor_aliasing_guards_on_parameters
                    and (
                        istype(value, torch.nn.Parameter)
                        or is_from_unspecialized_builtin_nn_module_source(
                            guard.originating_source
                        )
                    )
                ) and not isinstance(guard.originating_source, NumpyTensorSource):
                    # Keep track of all the tensor guard managers to insert
                    # NoAliasing check at the end.
                    self.no_tensor_aliasing_names.append(tensor_name)
                    self.no_tensor_aliasing_guard_managers.append(guard_manager)

                output_graph = self.check_fn_manager.output_graph
                metadata = output_graph.input_source_to_sizes_strides[
                    guard.originating_source
                ]
                size = convert_to_concrete_values(metadata["size"])
                stride = convert_to_concrete_values(metadata["stride"])

                verbose_code_parts = get_verbose_code_parts(
                    get_tensor_guard_code_part(
                        value,
                        tensor_name,
                        size,
                        stride,
                        pytype,
                        dispatch_keys,
                    ),
                    guard,
                )
                user_stack = guard.user_stack
                guard_manager.add_tensor_match_guard(
                    value,
                    size,  # type: ignore[arg-type]
                    stride,  # type: ignore[arg-type]
                    tensor_name,
                    verbose_code_parts,
                    user_stack,
                    pytype,
                    dispatch_keys,
                )

                # We consider TENSOR_MATCH guard to be important enough to be
                # included in diff guard manager by default.
                if not isinstance(value, torch.nn.Parameter):
                    self.guard_manager.diff_guard_sources.add(guard.name)

            # A frame is valid for reuse with dynamic dimensions if the new
            # (user-requested) dynamic dimensions are a subset of the old
            # (already compiled) dynamic dimensions.
            #
            # It's a little non-obvious why you'd want this: in particular,
            # if an already compiled frame matches all of the guards, why
            # not just use it, why force a recompile?
            #
            # We force it for two reasons:
            #
            #   - The user *required* us to compile with a new dynamic dimension,
            #     we should not ignore that and serve up the old, specialized
            #     frame.  Listen to the user!
            #
            #   - In fact, we are obligated to *raise an error* if we fail to
            #     make the requested dimension dynamic.  If we don't
            #     recompile, we can't tell if that dimension can actually be
            #     made dynamic.
            #
            # If the new dynamic dims are a subset of the old, we already know
            # we can make them dynamic (since we made them dynamic in old).
            # This is slightly unsound, because maybe your input size is
            # [s0, s0, s1] and so you can do it dynamic if you say dynamic
            # dims {0, 1, 2} but you can't if you only do {0, 2} (because now
            # the second s0 is specialized).  But we're not entirely sure if
            # this is a good idea anyway lol... (if you want to try removing
            # this logic, be my guest!  -- ezyang 2024)
            #
            assert guard.source is not None
            static, _reason = tensor_always_has_static_shape(
                value, is_tensor=True, tensor_source=guard.originating_source
            )

            if not static:
                if hasattr(value, "_dynamo_dynamic_indices"):
                    dynamic_indices = value._dynamo_dynamic_indices
                    code_part = f"(({tensor_name}._dynamo_dynamic_indices.issubset({dynamic_indices})) if hasattr({tensor_name}, '_dynamo_dynamic_indices') else True)"
                    code.append(code_part)
                    self.get_guard_manager(guard).add_dynamic_indices_guard(
                        dynamic_indices,
                        get_verbose_code_parts(code_part, guard),
                        guard.user_stack,
                    )
                # In the case of us not having any dynamic dimension indices, we compiled the frame with no chance of
                # raising for this specific tensor - and any inputs with more dynamic user directives specified must be recompiled.
                else:
                    code_part = (
                        f"hasattr({tensor_name}, '_dynamo_dynamic_indices') == False"
                    )
                    code.append(code_part)
                    self.get_guard_manager(guard).add_no_hasattr_guard(
                        "_dynamo_dynamic_indices",
                        get_verbose_code_parts(code_part, guard),
                        guard.user_stack,
                    )

                # Guard on shape_ids for tensors marked with mark_unbacked().
                # - If the runtime tensor has _dynamo_unbacked_indices → check shape_ids match
                # - If the runtime tensor doesn't have _dynamo_unbacked_indices → pass
                # We must install guards even when shape_ids is None to detect runtime
                # tensors that have the attribute when compile-time didn't.
                if hasattr(value, "_dynamo_unbacked_indices"):
                    shape_ids = getattr(value, "_dynamo_shape_ids", None)
                    code_part = f"((getattr({tensor_name}, '_dynamo_shape_ids', None) == {shape_ids!r}) if hasattr({tensor_name}, '_dynamo_unbacked_indices') else True)"
                    code.append(code_part)
                    self.get_guard_manager(guard).add_lambda_guard(
                        lambda x, expected=shape_ids: (
                            getattr(x, "_dynamo_shape_ids", None) == expected
                            if hasattr(x, "_dynamo_unbacked_indices")
                            else True
                        ),
                        get_verbose_code_parts(code_part, guard),
                        guard.user_stack,
                    )

                # Guard on unbacked_bounds for tensors marked with mark_unbacked().
                # - If the runtime tensor has _dynamo_unbacked_indices → check bounds match
                # - If the runtime tensor doesn't have _dynamo_unbacked_indices → pass
                # We must install guards even when unbacked_bounds is None to detect runtime
                # tensors that have the attribute when compile-time didn't.
                if hasattr(value, "_dynamo_unbacked_indices"):
                    unbacked_bounds = getattr(value, "_dynamo_unbacked_bounds", None)
                    code_part = f"((getattr({tensor_name}, '_dynamo_unbacked_bounds', None) == {unbacked_bounds!r}) if hasattr({tensor_name}, '_dynamo_unbacked_indices') else True)"
                    code.append(code_part)
                    self.get_guard_manager(guard).add_lambda_guard(
                        lambda x, expected=unbacked_bounds: (
                            getattr(x, "_dynamo_unbacked_bounds", None) == expected
                            if hasattr(x, "_dynamo_unbacked_indices")
                            else True
                        ),
                        get_verbose_code_parts(code_part, guard),
                        guard.user_stack,
                    )

                # TODO we dont have guards on _dynamo_unbacked_indices like those of _dynamo_dynamic_indices this seems wrong!!

            if len(code) > 0:
                self._set_guard_export_info(guard, code)
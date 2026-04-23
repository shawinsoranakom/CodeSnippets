def call_setattr(
        self,
        tx: "InstructionTranslator",
        obj: VariableTracker,
        name_var: VariableTracker,
        val: VariableTracker,
    ) -> VariableTracker | None:
        if isinstance(
            obj,
            (
                variables.DefaultDictVariable,
                variables.UserDefinedObjectVariable,
                variables.NestedUserFunctionVariable,
                variables.ExceptionVariable,
                variables.TracebackVariable,
            ),
        ):
            return obj.call_method(tx, "__setattr__", [name_var, val], {})
        elif (
            tx.output.side_effects.is_attribute_mutation(obj)
            and name_var.is_python_constant()
        ):
            name = name_var.as_python_constant()
            if obj.is_tensor():
                from .builder import wrap_fx_proxy

                # Some special handling for tensor attributes.
                if name == "requires_grad":
                    # TODO(voz): Make it work properly
                    unimplemented(
                        gb_type="setattr() on Tensor.requires_grad",
                        context=f"setattr({obj}, {name}, {val})",
                        explanation="setattr() on Tensor.requires_grad not supported. "
                        "Mutating requires_grad can introduce a new leaf from non-leaf or vice versa in "
                        "the middle of the graph, which AOTAutograd does not currently know how to handle.",
                        hints=[*graph_break_hints.SUPPORTABLE],
                    )
                elif name == "data":
                    # See comments on `test_set_data_on_scoped_tensor` for plans
                    # to support this.
                    if obj.source is None:
                        unimplemented(
                            gb_type="Failed to mutate tensor data attribute",
                            context=f"setattr({obj}, {name}, {val})",
                            explanation="Dyanmo only supports mutating `.data`"
                            " of tensor created outside `torch.compile` region",
                            hints=[
                                "Don't mutate `.data` on this tensor, or move "
                                "the mutation out of `torch.compile` region",
                            ],
                        )
                    elif obj.dtype != val.dtype:  # type: ignore[attr-defined]
                        unimplemented(
                            gb_type="Failed to mutate tensor data attribute to different dtype",
                            context=f"setattr({obj}, {name}, {val})",
                            explanation="Dyanmo only supports mutating `.data`"
                            " of tensor to a new one with the same dtype",
                            hints=[
                                "Don't mutate `.data` on this tensor, or move "
                                "the mutation out of `torch.compile` region",
                            ],
                        )

                    # Remove the old reference in tracked fakes - if we don't do this
                    # new .data value size and shape differences will cause
                    # tracked fakes to produce incorrect guards. This is sound because the TensorVariable
                    # coming out of set_() below will be a new one, and get
                    # installed in tracked fakes.
                    to_remove = [
                        tf for tf in tx.output.tracked_fakes if tf.source == obj.source
                    ]
                    for tf in to_remove:
                        tx.output.tracked_fakes.remove(tf)

                    # Step 1 - disable grads
                    with dynamo_disable_grad(tx), torch.no_grad():
                        # Step 2 - call `set_`
                        out = wrap_fx_proxy(
                            tx,
                            tx.output.create_proxy(
                                "call_function",
                                torch.Tensor.set_,
                                *proxy_args_kwargs([obj, val], {}),
                            ),
                        )

                    # Step 3 - drop the version counter - this is a step required to get
                    # .data setting to play correctly with the autograd engine.
                    # Essentially, dynamo is trying to faithfully preserve the (absurd)
                    # behavior of .data= from eager mode
                    def _lower_version_count_by_1(x: torch.Tensor) -> torch.Tensor:
                        version = x._version
                        if version > 0:
                            version = version - 1
                        torch._C._autograd._unsafe_set_version_counter((x,), (version,))
                        return x

                    tx.output.create_proxy(
                        "call_function",
                        _lower_version_count_by_1,
                        (out.as_proxy(),),
                        {},
                    )
                    _lower_version_count_by_1(obj.as_proxy().node.meta["example_value"])
                    # This handles options prop, guards and ends with a clone
                    # Step 4 - replace all reference to the current object with the new one
                    return out
                elif name in ("_grad", "grad"):
                    # NOTE: [Tensor "grad" and "_grad" attr]
                    # _grad and grad share the same setter/getter, see
                    # THPVariable_properties, and here we make sure setting one
                    # enables reading `val` from the other, by routing all
                    # read/write to `grad`.
                    name = "grad"
                elif is_tensor_getset_descriptor(name):
                    # Attribute like `torch.Tensor.real` has special setters we
                    # don't yet support; it's not as simple adding an entry to
                    # the side effect mapping.
                    unimplemented(
                        gb_type="Failed to set tensor attribute",
                        context=f"setattr({obj}, {name}, {val})",
                        explanation="Dyanmo doesn't support setting these tensor attributes",
                        hints=[
                            f"Don't mutate attribute '{name}' on tensors, or "
                            "move the mutation out of `torch.compile` region",
                        ],
                    )

            tx.output.side_effects.store_attr(obj, name, val)
            return val
        elif isinstance(obj, variables.NNModuleVariable):
            if not tx.output.is_root_tracer():
                unimplemented(
                    gb_type="nn.Module mutation in HigherOrderOp",
                    context=f"nn.Module: {obj}",
                    explanation="Inplace modifying nn.Module params/buffers inside HigherOrderOps is not allowed.",
                    hints=[
                        "Remove the mutation or move it outside of the HigherOrderOp.",
                        *graph_break_hints.FUNDAMENTAL,
                    ],
                )
            if name_var.is_python_constant() and isinstance(
                val, variables.TensorVariable
            ):
                assigning_fake_val = get_fake_value(val.as_proxy().node, tx)

                try:
                    getattr_var = obj.var_getattr(tx, name_var.as_python_constant())
                except (AttributeError, ObservedAttributeError):
                    getattr_var = None

                if getattr_var is not None and getattr_var.is_tensor():
                    # get_fake_val will get the same fake tensor
                    existing_fake_attr = get_fake_value(getattr_var.as_proxy().node, tx)

                    # same tensor identity, setattr is a no-op
                    mod_setattr = inspect.getattr_static(obj.module_type, "__setattr__")
                    if (
                        existing_fake_attr is assigning_fake_val
                        and mod_setattr is torch.nn.Module.__setattr__
                    ):
                        return getattr_var

            obj.convert_to_unspecialized(tx)
        return None
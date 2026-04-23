def _call_nonstrict_traceable_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: "dict[str, VariableTracker]",
    ) -> VariableTracker:
        from torch._dynamo.utils import _make_inlined
        from torch._higher_order_ops.flat_apply import (
            flat_apply,
            is_graphable_type,
            is_valid_output,
            to_graphable,
        )
        from torch._higher_order_ops.invoke_leaf_function import _LeafCallable
        from torch._subclasses.fake_tensor import fake_tensor_tls
        from torch.utils._pytree import tree_flatten

        from .base import AsPythonConstantNotImplementedError
        from .builder import SourcelessBuilder, wrap_fx_proxy

        # 1. Convert `args, kwargs` into pytree-flattened proxy forms.
        #
        # Rather than reconstructing `args, kwargs` into python objects and
        # then tree_flatten them, we just let Dynamo symbolically interpret
        # `tree_flatten((args, kwargs))`. This saves us from having to
        # worry about the reconstruction logic, side effects, and guards.
        args_with_states, kwargs_with_states = self._extract_nn_module_states(
            tx, args, kwargs
        )
        flat_args_vts, input_spec_vt = _make_inlined(tx, tree_flatten)(
            VariableTracker.build(tx, (args_with_states, kwargs_with_states))
        ).unpack_var_sequence(tx)
        assert isinstance(flat_args_vts, ListVariable)

        # Handle the case when the input contains a non-graphable type.
        for flat_arg_vt in flat_args_vts.items:
            arg_type = flat_arg_vt.python_type()
            if not is_graphable_type(arg_type):
                type_name = flat_arg_vt.python_type().__qualname__
                unimplemented(
                    gb_type="Invalid input type for nonstrict_trace-ed function",
                    context=f"Encountered input of type <{type_name}>.",
                    explanation=(
                        "For `nonstrict_trace`-ed functions, only basic types (e.g., torch.Tensor, int, float) "
                        "or pytree containers of those are allowed as inputs. The provided argument contains "
                        "an unsupported type."
                    ),
                    hints=[
                        "Use one of the following to register the type with pytree:\n"
                        "* `torch.utils._pytree.register_constant`\n"
                        "* `torch.utils._pytree.register_dataclass`\n"
                        "* `torch.utils._pytree.register_pytree_node`",
                    ],
                )

        # Since we checked with `is_graphable` above, `as_proxy` on the
        # flat_arg VT should always work.
        proxified_flat_args = [
            flat_arg_vt.as_proxy() for flat_arg_vt in flat_args_vts.items
        ]

        # The downstream `flat_apply` call requires the input spec; however,
        # the spec not a graphable type, so we still have to reconstruct it
        # into a python object, and store it as a constant attribute on the
        # fx graph.
        try:
            input_spec = input_spec_vt.as_python_constant()
        except AsPythonConstantNotImplementedError as e:
            typ = e.vt.python_type()
            type_name = typ.__qualname__
            import torch.utils._pytree as pytree

            if pytree.is_constant_class(typ):
                unimplemented(
                    gb_type="Input marked with `pytree.register_constant` constructed in the `torch.compile` region",
                    context=f"Input={input_spec_vt}, offending type <{type_name}>.",
                    explanation=(
                        "Calling a `nonstrict_trace`-ed function with an input that contains an object "
                        f"of type <{type_name}>, which was marked with `pytree.register_constant`. However, the object "
                        "was constructed _inside_ the `torch.compile` region. This is not supported."
                    ),
                    hints=[
                        "Construct the object _outside_ the `torch.compile` region, or submit an issue to GitHub.",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                    from_exc=e,
                )
            else:
                unimplemented(
                    gb_type="Invalid use of pytree_flatten with nonstrict_trace-ed function",
                    context=f"Input={input_spec_vt}, offending type <{type_name}>.",
                    explanation=(
                        "Calling a `nonstrict_trace`-ed function where one of the inputs has been registered "
                        f"with a `pytree_flatten` that places an object of type <{type_name}> into the context."
                    ),
                    hints=[
                        "Modifying the `pytree_flatten` to avoid placing the object into the context.",
                        f"Apply one of the following to <{type_name}>:\n"
                        "* `torch.utils._pytree.register_constant`\n"
                        "* `torch.utils._pytree.register_dataclass`\n"
                        "* `torch.utils._pytree.register_pytree_node`",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                    from_exc=e,
                )

        fn = self.value

        def patched_fn(
            *args: VariableTracker, **kwargs: VariableTracker
        ) -> VariableTracker:
            # This enables reads to global/captured tensors, and we'll just
            # treat them as constants in the graph. Note that after
            # AOTDispatcher, this logic would disappear.
            old_val = fake_tensor_tls.allow_non_fake_inputs_override
            fake_tensor_tls.allow_non_fake_inputs_override = True
            try:
                res = fn(*args, **kwargs)
            finally:  # reset even when `fn` raises
                fake_tensor_tls.allow_non_fake_inputs_override = old_val
            return res

        f_callable = _LeafCallable(patched_fn)

        f_callable_proxy = tx.output.register_static_attr_and_return_proxy(
            f"{fn.__name__}_callable", f_callable
        )
        input_spec_proxy = tx.output.register_static_attr_and_return_proxy(
            fn.__name__ + "_input_spec",
            # pyrefly: ignore [unbound-name]
            input_spec,
        )
        f_callable_proxy.node.type = type(f_callable)
        # pyrefly: ignore [unbound-name]
        input_spec_proxy.node.type = type(input_spec)
        all_args = (f_callable_proxy, input_spec_proxy, *proxified_flat_args)

        # 2. Create a proxy call to `flat_apply`, then fake-tensor propagate
        # the call and wrap output into a VariableTracker.

        # What's going on here? The output of the nonstrict-traced function must
        # be something we can put into the graph. This means it has to be Tuple,
        # int, str, etc or lists/tuples of those (or lists of lists of those,
        # etc). So by default we don't handle PyTree-able outputs.

        # To handle PyTree-able outputs we flatten the output to a flattened
        # list of graph types and then trace the unflattening into the graph.
        captured_spec: TreeSpec | None = None

        def flat_apply_capture(*args: Any) -> list[object]:
            nonlocal captured_spec
            out = flat_apply(*args, checked_output=False)
            # Output is handled similar to flat_apply input but reverse by
            # tree_flattening the output and trace the unflattening. Note that
            # wrapped functions must return the same pytree structure every time
            # they're called.
            flat_out, spec = to_graphable(out)
            if captured_spec is None:
                captured_spec = spec
            else:
                assert captured_spec == spec, (
                    "Error: nonstrict-traced functions must return the same "
                    f"output shape every time. got {spec!r} vs but expected {captured_spec!r}"
                )
            assert is_valid_output(flat_out)
            return flat_out

        proxy = tx.output.create_proxy(
            "call_function", flat_apply_capture, all_args, {}
        )

        # Instead of calling tree_unflatten at runtime, symbolically trace it
        # just like we did for tree_flatten on inputs. This lets Dynamo
        # capture the unflatten into the FX graph as well.

        # Build VTs representing (flat_output_list, out_spec)
        try:
            proxy_list_vt = wrap_fx_proxy(tx, proxy)
        except (
            # From `handle_traced_output`.
            torch._dynamo.exc.Unsupported,
            # From `flat_apply` assert on output type.
            torch._dynamo.exc.TorchRuntimeError,
        ):
            unimplemented(
                gb_type="Unsupported output type for nonstrict_trace-ed function",
                context=f"Function: {fn.__name__}",
                explanation=(
                    "For `nonstrict_trace`-ed functions, only basic types (e.g., torch.Tensor, int, list)"
                    " are allowed as output. The result of this call contains an unsupported type."
                ),
                hints=[*graph_break_hints.SUPPORTABLE],
            )
            # pyrefly error: why doesn't it recognize unimplemented() as NoReturn?
            raise AssertionError("unreachable")  # noqa: B904

        assert captured_spec is not None
        out_spec_vt = VariableTracker.build(tx, captured_spec)

        # Reuse the same pattern used above for tree_flatten: call the python
        # function through Dynamo so it symbolically interprets it.
        out_vt = SourcelessBuilder.create(tx, _pytree.tree_unflatten).call_function(
            tx, [proxy_list_vt, out_spec_vt], {}
        )

        return out_vt
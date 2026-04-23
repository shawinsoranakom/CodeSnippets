def process_kernel(
        cls, kernel: _OpOverloads, *args: Any, **kwargs: Any
    ) -> tuple[
        Any,
        list[Any],
        list[Any],
        Callable[[Any, Any], Any],
        dict[sympy.Symbol, pytree.KeyPath] | None,
    ]:
        """Partition kernel args into tensor and non-tensor, realize tensor inputs,
        re-run fake tensor propagation with the realized strides, and return
        (example_output, tensor_args, non_tensor_args, unflatten_args, unbacked_bindings).

        unflatten_args(new_tensor_args, new_non_tensor_args) reconstructs the
        original (args, kwargs) tree from replacement lists.
        """
        binded_args = {"args": args, "kwargs": kwargs}

        args_flat, args_spec = pytree.tree_flatten(binded_args)

        args_flat_is_tensor: list[bool] = []
        # tensor_args can be either tensor or torchbind objects
        tensor_args: list[IRNode] = []
        non_tensor_args: list[object] = []
        real_non_tensor_args: list[
            FakeScriptObject
            | torch._C.Generator
            | torch._C.ScriptObject
            | torch.Tensor
            | IntLikeType
        ] = []
        for arg in args_flat:
            match arg:
                case Expr():
                    node = V.graph.sizevars.shape_env.create_symintnode(arg, hint=None)
                    args_flat_is_tensor.append(False)
                    non_tensor_args.append(node)
                    real_non_tensor_args.append(node)

                case GeneratorState():
                    args_flat_is_tensor.append(False)
                    non_tensor_args.append(arg)
                    device_index = arg.device.index
                    assert arg.device.type == "cuda" and device_index is not None
                    real_non_tensor_args.append(
                        torch.cuda.default_generators[device_index].clone_state()
                    )

                case OpaqueObjectState():
                    args_flat_is_tensor.append(False)
                    non_tensor_args.append(arg)
                    real_non_tensor_args.append(arg.value)

                case IRNode():
                    args_flat_is_tensor.append(True)
                    tensor_args.append(arg)

                case _:
                    args_flat_is_tensor.append(False)
                    non_tensor_args.append(arg)
                    real_non_tensor_args.append(arg)

        def unflatten_args(
            new_tensor_args: Sequence[_T], new_non_tensor_args: Sequence[_T]
        ) -> tuple[list[_T], dict[str, _T]]:
            result = []
            it_tensors = iter(new_tensor_args)
            it_non_tensors = iter(new_non_tensor_args)
            for is_tensor in args_flat_is_tensor:
                if is_tensor:
                    result.append(next(it_tensors))
                else:
                    result.append(next(it_non_tensors))
            r = pytree.tree_unflatten(result, args_spec)
            return r.get("args", []), r.get("kwargs", {})

        tensor_args = [cls.realize_input(x) for x in tensor_args]

        # freeze layout otherwise our output stride calculation might
        # become incorrect
        for x in tensor_args:
            if is_storage_and_layout(x):
                as_storage_and_layout(x, freeze=True)

        # Rerun fake tensor propagation, because Inductor may have changed the
        # strides of inputs and we need to determine accurately what the
        # output stride will be.
        example_args: list[
            torch.Tensor | torch._C.ScriptObject | FakeScriptObject | torch.Generator
        ] = []

        # We need to retain the constant values of fake tensors that we originally
        # propagated the graph with, because for some operators running without a
        # constant would trigger an error / DataDependentException
        for x in tensor_args:
            # if x is a view of a constant, we need to realize the view
            # (we can't pass the constant into the kernel directly)
            if not isinstance(x, BaseView) and x.get_name() in V.graph.constants:
                example_args.append(V.graph.constants[x.get_name()])
            elif (
                not isinstance(x, BaseView)
                and x.get_name() in V.graph.torchbind_constants
            ):
                example_args.append(V.graph.torchbind_constants[x.get_name()])
            elif isinstance(x, TorchBindObject):
                example_args.append(x.get_value())
            elif isinstance(x, OpaqueMultiOutput):
                example_args.append(x.opaque_example_value)
            elif isinstance(x, torch._inductor.ir.GeneratorState):
                device_index = x.device.index
                assert x.device.type == "cuda" and device_index is not None
                example_args.append(
                    torch.cuda.default_generators[device_index].clone_state()
                )
            else:
                example_args.append(ir_node_to_tensor(x))

        new_args, new_kwargs = unflatten_args(example_args, real_non_tensor_args)
        example_output = kernel(*new_args, **new_kwargs)

        unbacked_bindings: dict[sympy.Symbol, pytree.KeyPath] | None = None
        if shape_env := V.fake_mode.shape_env:
            node_meta_val = V.current_node.meta.get("val")
            ctx: AbstractContextManager[None] = nullcontext()
            if V.current_node.target is torch._higher_order_ops.effects.with_effects:
                # remove the first effect token in meta["val"] and meta["unbacked_bindings"]
                node_meta_val = node_meta_val[1]
                ctx = _remove_effect_token_unbacked_bindings(V.current_node)

            with ctx:
                rebind_unbacked(shape_env, V.current_node, example_output)
            unbacked_bindings = compute_unbacked_bindings(
                shape_env, example_output, node_meta_val
            )

        example_out_li = (
            [example_output]
            if not isinstance(example_output, (list, tuple))
            else example_output
        )
        # When graph_partition is enabled, skip - partitioning handles sparse outputs
        for t in example_out_li:
            if (
                isinstance(t, torch.Tensor)
                and t.is_sparse
                and not config.graph_partition
            ):
                msg = "sparsity not handled. Please file issue for sparse inference weights."
                if stack_trace := V.graph.current_node.meta.get("stack_trace", None):
                    msg = f"{msg} Found from : \n {stack_trace}"
                V.graph.disable_cudagraphs_reason = msg

        return (
            example_output,
            tensor_args,
            non_tensor_args,
            unflatten_args,
            unbacked_bindings,
        )
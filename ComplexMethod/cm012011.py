def create(cls, kernel: _OpOverloads, *args: Any, **kwargs: Any) -> FallbackKernel:
        """Create an instance of FallbackKernel from an _OpOverloads"""
        fake_incorrect_kernels = (aten._fused_moving_avg_obs_fq_helper_functional,)
        if kernel not in fake_incorrect_kernels:
            context = cast(AbstractContextManager[None], V.graph.fake_mode)
        else:
            context = nullcontext()

        with context:
            (
                example_output,
                tensor_args,
                non_tensor_args,
                unflatten_args,
                unbacked_bindings,
            ) = cls.process_kernel(kernel, *args, **kwargs)

        # Try to lower single output functional custom ops to their out-variant.
        if (
            isinstance(kernel, torch._ops.OpOverload)
            and not torch._library.utils.is_builtin(kernel)
            and isinstance(example_output, torch.Tensor)
        ):
            from torch._library._out_variant import (
                _is_functional,
                get_out_arg_names,
                lookup_manual_out_variant,
                to_out_variant,
            )

            out_op = None
            if _is_functional(kernel._schema):
                out_op = to_out_variant(kernel)
            if out_op is None:
                out_op = lookup_manual_out_variant(kernel)

            if out_op is not None and len(get_out_arg_names(out_op)) == 1:
                layout = FixedLayout(
                    device=example_output.device,
                    dtype=example_output.dtype,
                    size=[*example_output.shape],
                    stride=[*example_output.stride()],
                )
                return ExternKernelOut(  # type: ignore[return-value]
                    layout=layout,
                    inputs=list(tensor_args),
                    constant_args=list(non_tensor_args),
                    kwargs=kwargs,
                    python_kernel_name=_make_out_variant_kernel_name(out_op),
                    op_overload=out_op,
                )

        # We need this extra check for input alignment since the example
        # inputs we created are always aligned.
        has_unaligned_input = any(is_unaligned(arg) for arg in tensor_args)

        device = cls.find_device(tensor_args, example_output)

        # Default to CPU for torchbind methods or HOPs that don't produce tensors
        if not device and (
            isinstance(kernel, torch._higher_order_ops.torchbind.CallTorchBind)
            or kernel is torch.ops.higher_order.print
        ):
            device = torch.device("cpu")

        # Try multi-output .out() lowering for custom ops with the out tag.
        if (
            isinstance(kernel, torch._ops.OpOverload)
            and not torch._library.utils.is_builtin(kernel)
            and not V.graph.cpp_wrapper
            and device
        ):
            out_result = ExternKernelMultiOut.try_create(
                kernel,
                example_output,
                device,
                tensor_args,
                non_tensor_args,
                unflatten_args,
                kwargs,
                unbacked_bindings=unbacked_bindings,
                has_unaligned_input=has_unaligned_input,
            )
            if out_result is not None:
                return out_result  # type: ignore[return-value]

        if example_output is None:
            packed = cls(
                NoneLayout(device=device),
                kernel,
                tensor_args,
                non_tensor_args,
                unflatten_args,
                kwargs=kwargs,
                unbacked_bindings=unbacked_bindings,
            )

        else:
            assert device, "Not sure where to find device info"
            packed = cls(
                MultiOutputLayout(device=device),
                kernel,
                tensor_args,
                non_tensor_args,
                unflatten_args,
                kwargs=kwargs,
                unbacked_bindings=unbacked_bindings,
            )

        def generate_output(output: Any, indices: list[tuple[Any, int]]) -> Any:
            if isinstance(output, (list, tuple)):
                return type(output)(
                    generate_output(output[i], indices + [(type(output), i)])
                    for i in range(len(output))
                )
            elif isinstance(output, dict):
                return {
                    key: generate_output(val, indices + [(type(output), key)])
                    for key, val in output.items()
                }
            elif isinstance(output, torch.Tensor):
                buf = MultiOutput(
                    cls.tensor_to_layout(output),
                    packed,
                    indices,
                )
                if (
                    config.assume_unaligned_fallback_output
                    or has_unaligned_input
                    or not tensor_is_aligned(output)
                ):
                    V.graph.unaligned_buffers.add(buf.name)  # type: ignore[arg-type]
                return buf
            elif isinstance(output, int):
                return output
            elif isinstance(output, torch.SymInt):
                return output.node.expr
            elif isinstance(
                output, (torch._C.ScriptObject, FakeScriptObject)
            ) or is_opaque_value(output):
                return OpaqueMultiOutput(
                    NoneLayout(device=device),
                    packed,
                    indices,
                    output,
                )
            else:
                assert output is None, (
                    f"FallbackKernel output type {type(output)} is not supported"
                )
                return None

        outputs = generate_output(example_output, [])
        if isinstance(outputs, (list, tuple)):
            packed.outputs = outputs
        elif isinstance(outputs, dict):
            packed.outputs = tuple(outputs)
        else:
            packed.outputs = [outputs]

        return outputs
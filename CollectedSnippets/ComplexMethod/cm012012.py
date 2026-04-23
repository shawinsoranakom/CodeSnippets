def try_create(
        cls,
        kernel: torch._ops.OpOverload,
        example_output: Any,
        device: torch.device,
        tensor_args: Sequence[IRNode],
        non_tensor_args: Sequence[Any],
        unflatten_args: Callable[..., Any],
        kwargs: dict[str, Any] | None,
        *,
        unbacked_bindings: dict[sympy.Symbol, pytree.KeyPath] | None = None,
        has_unaligned_input: bool = False,
    ) -> Sequence[AllocatingMultiOutput] | None:
        """Create an ExternKernelMultiOut if the op has a matching .out() variant."""
        from torch._library._out_variant import (
            _is_functional,
            get_out_arg_names,
            to_out_variant,
        )

        if not _is_functional(kernel._schema):
            return None

        if not isinstance(example_output, (tuple, list)):
            return None

        out_op = to_out_variant(kernel)
        if out_op is None:
            return None

        out_arg_names = get_out_arg_names(out_op)
        if not all(isinstance(t, torch.Tensor) for t in example_output):
            return None
        if len(example_output) != len(out_arg_names):
            return None

        packed = cls(
            MultiOutputLayout(device=device),
            kernel,
            tensor_args,
            non_tensor_args,
            unflatten_args,
            kwargs=kwargs,
            unbacked_bindings=unbacked_bindings,
            out_op=out_op,
            out_arg_names=out_arg_names,
        )

        outputs: list[AllocatingMultiOutput] = []
        for i, tensor_out in enumerate(example_output):
            layout = FixedLayout(
                device=tensor_out.device,
                dtype=tensor_out.dtype,
                size=[*tensor_out.shape],
                stride=[*tensor_out.stride()],
            )
            multi_out = AllocatingMultiOutput(
                layout=layout,
                input=packed,
                indices=[(type(example_output), i)],
            )
            if (
                config.assume_unaligned_fallback_output
                or has_unaligned_input
                or not tensor_is_aligned(tensor_out)
            ):
                V.graph.unaligned_buffers.add(multi_out.name)  # type: ignore[arg-type]
            outputs.append(multi_out)

        packed.out_variant_output_nodes = outputs
        packed.outputs = outputs

        if isinstance(example_output, tuple):
            return tuple(outputs)  # type: ignore[return-value]
        return list(outputs)
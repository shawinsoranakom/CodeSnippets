def create_out_of_place(
        cls,
        kernel: _OpOverloads,
        inputs: TensorBox | list[TensorBox],
        *args: Any,
        **kwargs: Any,
    ) -> list[MultiOutput] | _CollectiveKernel:
        with V.graph.fake_mode:
            (
                example_output,
                tensor_args,
                non_tensor_args,
                unflatten_args,
                unbacked_bindings,
            ) = cls.process_kernel(kernel, inputs, *args, **kwargs)
        assert not unbacked_bindings, f"{kernel}, {unbacked_bindings}"
        for tensor_arg in tensor_args:
            if not isinstance(tensor_arg, TorchBindObject):
                tensor_arg.realize()

        if isinstance(example_output, list):
            device = cls.find_device(tensor_args, example_output)
            assert device is not None
            packed = cls(
                MultiOutputLayout(device=device),
                kernel,
                tensor_args,
                non_tensor_args,
                unflatten_args,
            )
            packed.outputs = [
                MultiOutput(
                    cls.tensor_to_layout(tensor),
                    packed,
                    [(list, i)],
                )
                for i, tensor in enumerate(example_output)
            ]
            for buf, tensor in zip(packed.outputs, example_output):
                if config.assume_unaligned_fallback_output or not tensor_is_aligned(
                    tensor
                ):
                    V.graph.unaligned_buffers.add(buf.name)  # type: ignore[arg-type]
            return packed.outputs
        else:
            packed = cls(
                cls.tensor_to_layout(example_output),
                kernel,
                tensor_args,
                non_tensor_args,
                unflatten_args,
            )
            if config.assume_unaligned_fallback_output or not tensor_is_aligned(
                example_output
            ):
                V.graph.unaligned_buffers.add(packed.name)  # type: ignore[arg-type]
            packed.outputs = [packed]
            return packed
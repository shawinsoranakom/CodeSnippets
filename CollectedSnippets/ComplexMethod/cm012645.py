def _generate_extern_kernel_common(
        self, kernel: ir.ExternKernel, out_ir_node: ir.IRNode
    ) -> None:
        """
        Generates FX IR from either ExternKernelAlloc or ExternKernelOut.
        """

        # Get FX nodes corresponding to the call args.
        assert ir.is_node_sequence(kernel.inputs)
        tensor_nodes = tuple(self._generate_buffer(arg) for arg in kernel.inputs)
        if hasattr(kernel, "unflatten_args"):
            args, _ = kernel.unflatten_args(tensor_nodes, kernel.constant_args)
        else:
            args = tensor_nodes + tuple(kernel.constant_args)

        # Get the result buffer.
        # Some kernels write to a pre-existing output tensor via the "out" kwarg.
        # Materialize any IR nodes in kwargs to FX nodes (e.g., TensorBox -> Tensor).
        kwargs = {
            k: self._generate_buffer(v) if isinstance(v, ir.IRNode) else v
            for k, v in kernel.kwargs.items()
        }

        result_buffer: str | None = None
        if isinstance(kernel, ir.ExternKernelOut):
            kwargs["out"] = self.buffer_to_node[out_ir_node.codegen_reference()]
        elif isinstance(kernel.layout, (ir.Layout, ir.MultiOutputLayout)):
            result_buffer = kernel.get_name()
        elif isinstance(kernel.layout, ir.NoneLayout):
            pass
        else:
            raise NotImplementedError(f"Unrecognized output layout: {kernel.layout}")

        fx_node = self.gm.graph.call_function(
            kernel.op_overload,  # type: ignore[arg-type]
            args=args,
            kwargs=kwargs,
        )

        # Assign the result to the given name.
        if result_buffer:
            assert "out" not in kwargs, (
                f"Extern kernel '{kernel}' has both result and out kwarg. Expected only one."
            )
            fx_node.name = result_buffer
            self.buffer_to_node[result_buffer] = fx_node
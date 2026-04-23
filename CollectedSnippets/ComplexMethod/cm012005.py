def __init__(
        self,
        *,
        kernel_idx: int,
        grid: Any,
        tma_descriptor_metadata: dict[str, Any],
        kernel_args: dict[str, Any],
    ) -> None:
        inputs: list[IRNode] = []
        kwargs: dict[str, IRNode] = {}
        constant_args: list[IRNode] = []

        for k, v in kernel_args.items():
            if isinstance(v, TensorBox):
                t = InputsKernel.unwrap_storage_for_input(self.realize_input(v))
                if k in tma_descriptor_metadata:
                    t = TMADescriptor.create(t, tma_descriptor_metadata[k])
                inputs.append(t)
                kwargs[k] = t
            else:
                constant_args.append(v)
                kwargs[k] = v

        assert len(inputs) != 0
        self.device = inputs[0].get_device()

        assert isinstance(inputs, Sequence), type(inputs)
        super().__init__(
            None,
            NoneLayout(device=self.device),
            inputs,
            tuple(constant_args),
            kwargs,
        )
        self.kernel_idx = kernel_idx
        self.grid = grid

        kernel, configs, _, _ = self.get_kernel_and_metadata()

        # If we are autotuning, not all arguments will be passed
        assert hasattr(kernel, "arg_names")
        self.ordered_kwargs_for_cpp_kernel = [
            arg for arg in kernel.arg_names if arg in kernel_args
        ]

        from torch._higher_order_ops.triton_kernel_wrap import (
            identify_accessed_tensors,
            identify_triton_stores,
        )

        autotuned_kwargs = configs[0].kwargs if len(configs) > 0 else {}

        import ast

        # pyrefly: ignore [missing-attribute]
        self.kernel_src = kernel.src
        self.kernel_ast = ast.parse(self.kernel_src)
        self.kernel_stores = identify_triton_stores(self.kernel_src)
        self.kernel_args = kernel_args
        # names in `arg_accesses.read_writes` are names of formal arguments in the kernel's prototype
        self.arg_accesses = identify_accessed_tensors(
            kernel,
            {**kernel_args, **autotuned_kwargs},
            tma_descriptor_metadata,
        )

        # Filter to only tensor args: with Triton 3.7+, ordered_arg_names
        # includes scalars, so writes may reference non-tensor args like SymInts.
        self.mutable_args = [
            kernel_args[key.name]
            for key in self.arg_accesses.read_writes.writes
            if isinstance(kernel_args.get(key.name), TensorBox)
        ]

        self.mutation_outputs = [
            MutationOutput(NoneLayout(device=self.device), buf, self)
            for buf in self.mutable_args
        ]
        V.graph.register_operation(self)
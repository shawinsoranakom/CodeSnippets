def call_HOP(
        self,
        variable: "TritonKernelVariable",
        grids: Any,
        combined_args: dict[str, Any],
        tx: "InstructionTranslator",
    ) -> "variables.ConstantVariable":
        from .dicts import ConstDictVariable

        # as we can only pass tensors as non-const args in fx graph,
        # here we replace TMA descriptors
        # (TMADescriptorExperimentalVariable and TMADescriptorStableVariable
        # instances) with the underlying tensors, while moving the
        # TMA descriptor-related metadata to a separate argument,
        # so that we can reconstruct the TMA descriptors downstream
        tma_descriptor_metadata: TMADescriptorMetadata = {}
        for k in list(combined_args.keys()):
            v = combined_args[k]
            if isinstance(
                v, (TMADescriptorExperimentalVariable, TMADescriptorStableVariable)
            ):
                tma_descriptor_metadata[k] = v.to_metadata()
                combined_args[k] = v.get_tensor()

        combined_args_vt = {
            VariableTracker.build(tx, k): v for k, v in combined_args.items()
        }

        from torch._higher_order_ops.triton_kernel_wrap import (
            kernel_side_table,
            triton_kernel_wrapper_mutation,
        )

        # Combine args and kwargs and pass as a dict so that if user defined triton
        # kernel uses variables as 'grid' or 'kernel', it does not conflict with
        # parameters of the wrapper function
        constant_args = {
            k: v.as_python_constant()
            for k, v in combined_args.items()
            if isinstance(v, VariableTracker) and v.is_python_constant()
        }
        non_constant_args = {
            k: v
            for k, v in combined_args_vt.items()
            if not (isinstance(v, VariableTracker) and v.is_python_constant())
        }

        for v in non_constant_args.values():
            v = v.realize()
            if not (v.is_tensor() or v.is_symnode_like()):
                self.raise_unsupported(
                    f"Unexpected argument type for a Triton kernel: {repr(v)}."
                )

        constant_args_idx = kernel_side_table.add_constant_args(constant_args)
        meta = ConstDictVariable(non_constant_args, dict)
        tx.output.create_proxy(
            "call_function",
            triton_kernel_wrapper_mutation,
            (),
            {
                "kernel_idx": variable.kernel_idx,
                "constant_args_idx": constant_args_idx,
                "grid": grids,
                "tma_descriptor_metadata": tma_descriptor_metadata,
                "kwargs": meta.as_proxy(),
            },
        )

        return VariableTracker.build(
            tx,
            None,
        )
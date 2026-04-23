def _generate_lazy_launch(
        self,
        prefix: IndentedBuffer,
        wrapper: CppWrapperGpu,
        wrapper_arg_names: list[str],
        kernel_arg_names: list[str],
    ) -> None:
        """Generate kernel launch code for lazy-compiled kernels."""
        kernel_name = self.kernel_name
        signature = (self.triton_meta or {}).get("signature", {})
        tma_tensor_args = self.tma_tensor_args
        num_tma_tensor_args = len(tma_tensor_args)

        # wrapper_arg_names may include grid and TMA tensor args at the end;
        # only the leading portion maps 1:1 to kernel signature params.
        num_signature_args = len(wrapper_arg_names) - num_tma_tensor_args
        inductor_meta = self.inductor_meta or {}
        num_signature_args -= len(inductor_meta.get("extra_launcher_args", []))

        arg_type_lookup = dict(
            zip(wrapper_arg_names, self.arg_types[:num_signature_args])
        )

        # Identify TMA args — they are already passed as StableTMADescriptor params,
        # so we just unpack them directly (no need to reconstruct from tensors).
        tma_arg_names = OrderedSet(self._get_tma_args().keys())

        # Non-TMA args go through generate_args_decl
        non_tma_arg_names = [n for n in kernel_arg_names if n not in tma_arg_names]
        non_tma_arg_types = [
            arg_type_lookup[n] for n in non_tma_arg_names if n in arg_type_lookup
        ]
        non_tma_arg_sigs = [signature.get(n) for n in non_tma_arg_names]

        call_args_str = wrapper.generate_args_decl(
            prefix,
            non_tma_arg_names,
            non_tma_arg_types,
            non_tma_arg_sigs,
        )

        call_args_str = self._generate_lazy_tma_args(
            prefix, call_args_str, kernel_arg_names, tma_arg_names, signature
        )
        call_args_str = self._generate_lazy_scratch(prefix, wrapper, call_args_str)

        launch_args = (
            f"{kernel_name}, grid_0, grid_1, grid_2,"
            f" {kernel_name}_result.num_warps,"
            f" {kernel_name}_result.shared_mem,"
            f" kernel_args_, stream_"
        )

        prefix.splice(
            f"""\
            void* kernel_args_[] = {{{call_args_str}}};
            launchKernel({launch_args});
            """
        )
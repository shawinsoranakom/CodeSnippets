def _resolve_lazy_arg_names(self) -> tuple[list[str], list[str]]:
        """Compute wrapper and kernel arg names from triton_meta signature.

        Returns (wrapper_arg_names, kernel_arg_names) where:
        - wrapper_arg_names: params accepted by the C++ wrapper function
        - kernel_arg_names: params passed to the GPU kernel launch (non-constexpr only)
        """
        assert self.triton_meta is not None, (
            f"triton_meta is required for lazy compile of {self.kernel_name}"
        )
        signature = self.triton_meta.get("signature", {})
        inductor_meta = self.inductor_meta or {}
        extra_launcher_args_count = len(inductor_meta.get("extra_launcher_args", []))
        tma_tensor_args = self.tma_tensor_args
        num_tma_tensor_args = len(tma_tensor_args)

        internal_config_suffixes = ("BLOCK", "RSPLIT", "RSPLIT_SIZE")
        # Declared constexpr params (tl.constexpr in kernel signature) are excluded
        # from arg_types for user-defined kernels, while value-based constexpr params
        # (e.g. numel=1, arg=None) are still in arg_types.
        declared_constexpr_names = OrderedSet(
            inductor_meta.get("declared_constexpr_names", [])
        )
        wrapper_arg_names = []
        kernel_arg_names = []
        for name, sig_type in signature.items():
            if name.endswith(internal_config_suffixes):
                continue
            if sig_type != "constexpr":
                kernel_arg_names.append(name)
            if name not in declared_constexpr_names:
                wrapper_arg_names.append(name)

        num_wrapper_args = (
            len(self.arg_types) - extra_launcher_args_count - num_tma_tensor_args
        )
        if num_wrapper_args != len(wrapper_arg_names):
            raise AssertionError(
                f"Mismatch between ({num_wrapper_args}) arg_types and "
                f"{len(wrapper_arg_names)} wrapper_arg_names for {self.kernel_name}."
            )

        # Append grid args: passed to wrapper. Kernel args will handle grids separately.
        for i in range(extra_launcher_args_count):
            wrapper_arg_names.append(f"_grid_{i}")

        # Add TMA tensor args after grid args
        if tma_tensor_args:
            sig_tma_keys = list(self._get_tma_args().keys())
            assert list(tma_tensor_args.keys()) == sig_tma_keys, (
                f"TMA tensor args order mismatch for {self.kernel_name}: "
                f"{list(tma_tensor_args.keys())} vs signature order {sig_tma_keys}"
            )
        for desc_name in tma_tensor_args:
            wrapper_arg_names.append(f"_tma_tensor_{desc_name}")

        return wrapper_arg_names, kernel_arg_names
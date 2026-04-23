def save_gpu_kernel(self, stream, launcher):
        key = self.inductor_meta.get("kernel_name", None)  # unique kernel name
        assert key is not None, "kernel_name can not be None"
        params = {
            "mangled_name": (
                launcher.bin.metadata.name
                if hasattr(launcher.bin.metadata, "name")
                else launcher.bin.metadata["name"]
            ),
            "num_warps": (
                launcher.bin.num_warps
                if hasattr(launcher.bin, "num_warps")
                else launcher.bin.metadata.num_warps
            ),
            "shared_mem": (
                launcher.bin.shared
                if hasattr(launcher.bin, "shared")
                else launcher.bin.metadata.shared
            ),
            "stream": stream,
            # User defined triton kernels will have arbitrary kwarg names
            "config": config_to_dict(launcher.config),
            "inductor_meta": self.inductor_meta,
            "triton_meta": self.triton_meta,
            "def_args": launcher.def_args,
            "call_args": launcher.call_args,
            "global_scratch": launcher.global_scratch,
            "profile_scratch": launcher.profile_scratch,
        }

        from torch._inductor import config
        from torch._inductor.codecache import CudaKernelParamCache

        bin_type = {"hip": "hsaco", "xpu": XPU_KERNEL_FORMAT}.get(
            self.device_props.type, "cubin"
        )
        binary = launcher.bin.asm[bin_type]

        # ROCm multi-arch: capture LLVM IR
        if torch.version.hip and config.aot_inductor.emit_multi_arch_kernel:
            # Multi-arch ROCm: Capture LLVM IR for cross-architecture compilation
            asm_type = "ll"

            # llir is the key to obtain LLVM IR from triton
            asm = launcher.bin.asm.get("llir", None)

            # CRITICAL: Multi-arch compilation cannot proceed without LLVM IR
            # Fail fast with clear error message pointing to the issue
            if not asm:
                available_keys = list(launcher.bin.asm.keys())
                raise RuntimeError(
                    f"ROCm multi-arch requires LLVM IR, but none found. "
                    f"Available keys: {available_keys}. "
                    f"Triton may need to be patched to emit LLVM IR."
                )

        # Everything else: capture architecture-specific assembly
        else:
            asm_type = {"hip": "amdgcn", "cuda": "ptx", "xpu": "spv"}.get(
                self.device_props.type
            )
            asm = launcher.bin.asm.get(asm_type, None)

        CudaKernelParamCache.set(key, params, binary, bin_type, asm, asm_type)
        self.cuda_kernel_saved = True
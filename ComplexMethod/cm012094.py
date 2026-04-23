def set(
        cls,
        key: str,
        params: dict[str, str | None],
        cubin: str,
        bin_type: str,
        asm: str | None = None,
        asm_type: str | None = None,
    ) -> None:
        basename = None
        if config.aot_inductor.package_cpp_only:
            assert config.triton.unique_kernel_names, (
                "package_cpp_only requires triton kernel names to be unique"
            )
            assert params["mangled_name"], "Missing kernel name"
            basename = params["mangled_name"]

        _, bin_path = write(
            cubin,
            bin_type,
            hash_type=bin_type,
            specified_dir=split_aot_inductor_output_path(
                config.aot_inductor.output_path
            )[0],
            key=basename,
        )
        # Retrieve the basename again in case it is a generated hashcode
        basename, _ = get_name_and_dir_from_output_file_path(bin_path)

        if config.aot_inductor.emit_multi_arch_kernel:
            bin_type_to_ext = {
                "cubin": ".fatbin",
                XPU_KERNEL_FORMAT: ".spv",
                "hsaco": ".hsaco",
            }
            assert bin_type in bin_type_to_ext, (
                "multi_arch_kernel_binary only supported in CUDA/XPU/ROCm"
            )
            base_path, _ = os.path.splitext(bin_path)
            bin_path = base_path + bin_type_to_ext[bin_type]

        asm_path: str = ""

        # Kernel assembly/IR requirements for AOT Inductor:
        # - CUDA/XPU: Always require PTX/SPV
        # - ROCm multi-arch: Require LLVM IR (.ll) for bundle compilation
        if (
            config.aot_inductor.emit_multi_arch_kernel
            or config.aot_inductor.package_cpp_only
        ):
            # Allow ROCm single-arch to skip (asm=None OK), require for everything else
            if torch.version.hip is None or (asm and asm_type):
                assert asm, "Missing kernel assembly code"
                assert asm_type, "Missing kernel assembly type"

                # Cache directory mapping: asm_type → hash_type
                # Problem: LLVM IR extension ".ll" isn't a recognized cache category
                # Solution: Map to "code" (generic category for non-standard formats)
                # Recognized categories: "ptx", "amdgcn", "spv", "code"
                hash_kind = asm_type if asm_type in {"amdgcn", "ptx", "spv"} else "code"

                _, asm_path = write(
                    asm,
                    asm_type,
                    hash_type=hash_kind,
                    specified_dir=split_aot_inductor_output_path(
                        config.aot_inductor.output_path
                    )[0],
                    key=basename,
                )

        params[get_cpp_wrapper_cubin_path_name()] = bin_path
        params["asm"] = asm_path
        cls.cache[key] = params
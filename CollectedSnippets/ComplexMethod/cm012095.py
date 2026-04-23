def compile(
        cls,
        graph: GraphLowering,
        wrapper_code: str,
        kernel_code: str,
        serialized_extern_kernel_nodes: str | None,
        *,
        device_type: str,
        additional_files: list[str],
    ) -> list[str | Weights] | str:
        """
        Returns the .so path, or returns a list of files that were generated if
        config.aot_inductor.package=True.
        """
        generated_files: list[str | Weights] = additional_files  # type: ignore[assignment]

        _set_gpu_runtime_env()  # cpp_extension consults the env

        picked_vec_isa = pick_vec_isa()
        vec_isa_cmd_gen = CppBuilder(
            name="o",
            sources="i",
            BuildOption=CppTorchDeviceOptions(
                vec_isa=picked_vec_isa,
                device_type=device_type,
                aot_mode=graph.aot_mode,
            ),
        )
        # write function will calc source_code hash, the same source code with different
        # ISA level should be generate different hash.
        # So we need get a command_line which contains isa related parameter as a part of hash key.
        # And then pass the command_line to below write function as extra parameter to
        # guarantee the source code hash contains ISA difference.
        cpp_command = repr(vec_isa_cmd_gen.get_command_line())

        # Meta internal AOTInductor CPU
        use_relative_path = (
            config.is_fbcode() and device_type == "cpu" and graph.aot_mode
        )

        (
            specified_output_path,
            specified_artifact_name,
        ) = split_aot_inductor_output_path(config.aot_inductor.output_path)

        # TODO (benjaminglass1): the CMake packaging path doesn't support linking files
        # built with different flags.  Until that's implemented, append the kernel code
        # to the wrapper and build everything at max optimization.
        if config.aot_inductor.package_cpp_only:
            wrapper_code = "\n".join((wrapper_code, kernel_code))
            kernel_code = ""

        wrapper_key, wrapper_path = write(
            wrapper_code,
            "wrapper.cpp",
            extra=cpp_command,
            specified_dir=specified_output_path,
            key=config.aot_inductor.model_name_for_generated_files,
        )
        kernel_code = (
            f"// Triton kernels are embedded as comments in {wrapper_path}\n"
            + kernel_code
        )
        _, kernel_path = write(
            kernel_code,
            "kernel.cpp",
            extra=cpp_command,
            specified_dir=specified_output_path,
            key=config.aot_inductor.model_name_for_generated_files,
        )

        header_code = ""
        header_path = ""
        if not config.aot_inductor.dynamic_linkage:
            # to link statically, we also need a header file
            with open(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "csrc",
                    "inductor",
                    "aoti_runtime",
                    "model.h",
                )
            ) as f:
                # model_name_for_generated_files is guaranteed to be non-empty when compile_standalone
                model_class_name = config.aot_inductor.model_name_for_generated_files
                class_name = f"AOTInductorModel{model_class_name}"
                header_code = f.read()

                # we replace like this to avoid replacing
                # AOTInductorModelBase and AOTInductorModelKernelsBase
                header_code = (
                    header_code.replace("<AOTInductorModel>", f"<{class_name}>")
                    .replace("AOTInductorModel(", f"{class_name}(")
                    .replace("AOTInductorModel :", f"{class_name} :")
                )
                _, header_path = write(
                    header_code,
                    "h",
                    specified_dir=specified_output_path,
                    key=model_class_name,
                )

        # Log the AOTInductor wrapper and kernel code, if needed.
        with WritableTempFile("w+") as t:
            """
            Avoid "Permission denied error" on Windows:
            with tempfile.NamedTemporaryFile("w", suffix=".gv") as temp_file:
                # Not writable on Windows:
                # https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile

            Example:
                with WritableTempFile("w", suffix=".gv") as temp_file:
                    tree.to_dotfile(temp_file.name)
            """
            t.writelines((wrapper_code, "\n", kernel_code, "\n"))
            t.flush()
            V.debug.output_code(t.name, extension="cpp")

        if config.aot_inductor.package:
            generated_files.append(wrapper_path)
            if not config.aot_inductor.package_cpp_only:
                generated_files.append(kernel_path)
            if not config.aot_inductor.dynamic_linkage:
                generated_files.append(header_path)

        output_code_log.info("Wrapper code written to: %s", wrapper_path)
        output_code_log.info("Kernel code written to: %s", kernel_path)
        trace_structured(
            "graph_dump",
            lambda: {
                "name": "inductor_aot_wrapper_code",
                "type": "cpp",
                "filename": wrapper_path,
            },
            payload_fn=lambda: wrapper_code,
        )
        trace_structured(
            "graph_dump",
            lambda: {
                "name": "inductor_aot_kernel_code",
                "type": "cpp",
                "filename": kernel_path,
            },
            payload_fn=lambda: kernel_code,
        )
        if not config.aot_inductor.dynamic_linkage:
            output_code_log.info("Header code written to: %s", header_path)
            trace_structured(
                "graph_dump",
                lambda: {
                    "name": "inductor_aot_header_code",
                    "type": "cpp",
                    "filename": header_path,
                },
                payload_fn=lambda: header_code,
            )

        # We use a file lock below to protect FS operations. The lock file
        # is scoped to the 'key', so make sure the consts_s is protected
        # by the same lock:
        wrapper_path_operator = Path(wrapper_path)
        kernel_path_operator = Path(kernel_path)
        specified_sub_dir = wrapper_path_operator.parent / wrapper_key
        if not specified_sub_dir.exists():
            specified_sub_dir.mkdir(exist_ok=True)
        cmake_path = str(Path(specified_sub_dir) / "CMakeLists.txt")

        def _compile_consts(consts: bytes, platform: str) -> str:
            # Load from aot_inductor, and update the value on demand.
            use_asm_build: bool = config.aot_inductor.use_consts_asm_build

            if platform == "linux":
                if graph.mutated_buffers & OrderedSet(graph.constants.keys()):
                    # .data section is between .text and .bss. When the size of .data is large,
                    # during the linking, the relocation of .text against .bss may overflow.
                    # Rename it to .ldata so that it won't be in between the .text and .bss section
                    if len(consts) > 2_000_000_000:
                        raise ValueError(
                            "Models with buffer mutation included doesn't support constants greater than 2GB!"
                        )
                    section_attr = '.ldata, "aw"'
                else:
                    section_attr = '.lrodata, "a"'
                symbol_prefix = ""
            elif platform == "darwin":
                section_attr = "__DATA,__data"
                symbol_prefix = "_"
            elif platform == "win32":
                symbol_prefix = ""
                # ASM build is not supported on Windows, force use CPP build.
                use_asm_build = False
            else:
                raise RuntimeError(f"Unsupported platform: {platform}")

            # Intel compiler failed to compile this manually constructed assembly file.
            # Switch XPU to use consts cpp build.
            if device_type == "xpu":
                use_asm_build = False

            is_large_consts = len(consts) > 1024
            is_zero_size_consts = len(consts) == 0

            def format_consts_to_gnu_asm(
                consts: bytes,
                align_bytes: int,
                symbol_prefix: str,
                is_large_consts: bool,
            ) -> tuple[str, str]:
                consts_asm = f"\t.section\t{section_attr}\n"
                consts_asm += f"\t.balign {align_bytes}\n"
                consts_asm += f"\t.globl\t{symbol_prefix}_binary_constants_bin_start\n"
                consts_asm += f"{symbol_prefix}_binary_constants_bin_start:\n"
                if not is_large_consts:
                    for c in consts:
                        consts_asm += f"\t.byte {c}\n"
                    # Add one element even if constants are empty
                    # Otherwise assembler will not put them in data section
                    if not consts:
                        consts_asm += "\t.space 1\n"
                else:
                    consts_asm += "\t.quad 0x1234567899abcdef\n"
                    consts_asm += f"\t.space {len(consts) - 8}\n"
                consts_asm += f".globl\t{symbol_prefix}_binary_constants_bin_end\n"
                consts_asm += f"{symbol_prefix}_binary_constants_bin_end:\n"
                return consts_asm, "weights.S"

            # Use c++ to convert consts to object file can support more compilers, such as msvc and icx.
            def format_consts_to_cpp(
                consts: bytes, align_bytes: int, symbol_prefix: str
            ) -> tuple[str, str]:
                consts_size = len(consts)
                asan_attr = """#if defined(__clang__) || defined (__GNUC__)\t\n\
#define ATTRIBUTE_NO_SANITIZE_ADDRESS __attribute__((no_sanitize("address")))\t\n\
#else\t\n\
#define ATTRIBUTE_NO_SANITIZE_ADDRESS\t\n\
#endif\t\n\
\t\n\
ATTRIBUTE_NO_SANITIZE_ADDRESS\t\n"""
                const_cpp = asan_attr
                const_cpp += f"alignas({align_bytes}) extern "
                const_cpp += f"unsigned char {symbol_prefix}_binary_constants_bin_start[{consts_size}] = {{\t\n"
                count_bytes = 0
                for c in consts:
                    const_cpp += f"{c}, "
                    count_bytes = count_bytes + 1
                    if count_bytes % 16 == 0:
                        const_cpp += "\t\n"
                const_cpp += "};\t\n"
                const_cpp += f"alignas({align_bytes}) extern unsigned char * {symbol_prefix}_binary_constants_bin_end;\t\n"
                return const_cpp, "weights.cpp"

            def get_zero_consts_asm_code(
                align_bytes: int,
                symbol_prefix: str,
            ) -> tuple[str, str]:
                """
                This function handles zero-sized constants because the C++ standard prohibits zero-length arrays:
                https://stackoverflow.com/questions/9722632/what-happens-if-i-define-a-0-size-array-in-c-c

                On Windows (MSVC):
                    The compiler reports error C2466 for zero-sized arrays:
                    https://learn.microsoft.com/en-us/cpp/error-messages/compiler-errors-1/compiler-error-c2466
                    Solution: Use assembly compilation to handle this case.

                Why not use Win32 assembly for all paths?
                    ml64 only supports alignment up to 16 bytes, which isn't optimal for performance.

                Cross-platform implementation:
                    Linux: Added '-pedantic' to disable zero-sized arrays in C++ compiler
                    Windows: MSVC naturally rejects zero-sized arrays by default
                """
                if _IS_WINDOWS:
                    # Windows ml64 is max support align to 16, but it is no effect to zero size data.
                    asm_code = """
option casemap:none
.data
?_binary_constants_bin_start@@3PAEA:
align 16
?_binary_constants_bin_end@@3PAEA:
align 16
public ?_binary_constants_bin_start@@3PAEA
public ?_binary_constants_bin_end@@3PAEA
end
"""
                    asm_ext = "asm"
                else:
                    asm_code = f"\t.section\t{section_attr}\n"
                    asm_code += f"\t.balign {align_bytes}\n"
                    asm_code += (
                        f"\t.globl\t{symbol_prefix}_binary_constants_bin_start\n"
                    )
                    asm_code += f"{symbol_prefix}_binary_constants_bin_start:\n"
                    asm_code += f".globl\t{symbol_prefix}_binary_constants_bin_end\n"
                    asm_code += f"{symbol_prefix}_binary_constants_bin_end:\n"
                    asm_ext = "S"
                return asm_code, asm_ext

            if use_asm_build:
                consts_code, code_ext = format_consts_to_gnu_asm(
                    consts, ALIGN_BYTES, symbol_prefix, is_large_consts
                )
            else:
                if is_zero_size_consts:
                    consts_code, code_ext = get_zero_consts_asm_code(
                        ALIGN_BYTES, symbol_prefix
                    )
                else:
                    consts_code, code_ext = format_consts_to_cpp(
                        consts, ALIGN_BYTES, symbol_prefix
                    )

            _, consts_s = write(
                consts_code,
                code_ext,
                specified_dir=str(specified_sub_dir),
                key=config.aot_inductor.model_name_for_generated_files,
            )
            consts_s = Path(consts_s)
            object_build_options = CppTorchDeviceOptions(
                device_type=device_type,
                aot_mode=graph.aot_mode,
                compile_only=True,
                use_relative_path=use_relative_path,
            )
            object_builder = CppBuilder(
                name=str(consts_s.stem),
                sources=str(consts_s),
                output_dir=str(consts_s.parent),
                BuildOption=object_build_options,
            )
            consts_o = object_builder.get_target_file_path()
            if use_asm_build is False and is_zero_size_consts:
                run_asm_build_object(str(consts_s), consts_o, str(consts_s.parent))
            else:
                object_builder.build()

            if is_large_consts and use_asm_build:
                with open(consts_o, "r+b") as f:
                    f.seek(0)
                    hdr = f.read(1024)
                    # Search for magic number and write the actual data over it
                    start_idx = (
                        hdr.find(b"\xef\xcd\xab\x99\x78\x56\x34\x12")
                        if sys.byteorder == "little"
                        else hdr.find(b"\x12\x34\x56\x78\x99\xab\xcd\xef")
                    )
                    assert start_idx != -1
                    f.seek(start_idx)
                    pos = 0
                    while pos < len(consts):
                        rc = f.write(consts[pos:])
                        pos += rc

            # Remove the .S file to save space
            os.remove(consts_s)

            return consts_o

        from torch.utils._filelock import FileLock

        lock_dir = get_lock_dir()
        lock = FileLock(
            os.path.join(lock_dir, wrapper_key + ".lock"), timeout=LOCK_TIMEOUT
        )
        with lock:
            if serialized_extern_kernel_nodes:
                extern_kernel_nodes_json = str(
                    wrapper_path_operator.with_suffix(".json")
                )
                with open(extern_kernel_nodes_json, "w") as f:
                    f.write(serialized_extern_kernel_nodes)

                if config.aot_inductor.package:
                    generated_files.append(extern_kernel_nodes_json)

            metadata = config.aot_inductor.metadata
            metadata["AOTI_DEVICE_KEY"] = device_type

            # Add environment information to ensure .so compatibility
            metadata.update(get_device_information(device_type))

            # Save user provided metadata
            meta_json = str(
                wrapper_path_operator.with_name(
                    f"{wrapper_path_operator.stem}_metadata.json"
                )
            )
            for k, v in config.aot_inductor.metadata.items():
                assert isinstance(k, str) and isinstance(v, (str)), (
                    "Metadata must only contain strings"
                )

            with open(meta_json, "w") as f:
                f.write(json.dumps(config.aot_inductor.metadata))

            kernel_meta_json = str(
                kernel_path_operator.with_name(
                    f"{kernel_path_operator.stem}_metadata.json"
                )
            )
            shutil.copy(meta_json, kernel_meta_json)

            if config.aot_inductor.package:
                generated_files.append(meta_json)
                if not config.aot_inductor.package_cpp_only:
                    generated_files.append(kernel_meta_json)

            output_so = (
                config.aot_inductor.output_path
                if specified_artifact_name
                else str(wrapper_path_operator.with_suffix(".so"))
            )
            all_cuda = all(
                graph.get_original_value_of_constant(name).is_cuda
                for name in graph.constants
                if name not in graph.folded_constants
            )

            def _to_bytes(t: torch.Tensor, all_cuda: bool) -> bytes:
                def _pad_to_alignment(raw_bytes: bytes) -> bytes:
                    padded_bytes = raw_bytes.ljust(
                        (len(raw_bytes) + ALIGN_BYTES - 1) // ALIGN_BYTES * ALIGN_BYTES,
                        b"\x00",
                    )
                    return padded_bytes

                # This serializes the tensor's untyped_storage to bytes by accessing
                # the raw data of the underlying structure.
                import ctypes

                if t.numel() == 0:
                    return b""

                if t.is_mkldnn:
                    data_ptr = torch.ops.mkldnn.data_ptr(t)
                    nbytes = torch.ops.mkldnn._nbytes(t)
                else:
                    t_cpu = t.untyped_storage().cpu()
                    data_ptr = t_cpu.data_ptr()
                    nbytes = t_cpu.nbytes()

                raw_array = ctypes.cast(
                    data_ptr,
                    ctypes.POINTER(ctypes.c_ubyte * nbytes),
                )
                # pyrefly: ignore [missing-attribute]
                raw_bytes = bytes(raw_array.contents)
                return raw_bytes if all_cuda else _pad_to_alignment(raw_bytes)

            if (
                config.aot_inductor.package_constants_in_so
                or config.aot_inductor.package_constants_on_disk_format == "binary_blob"
            ):
                serialized_weights = b"".join(
                    _to_bytes(graph.get_original_value_of_constant(name), all_cuda)
                    for name in graph.constants
                    if name not in graph.folded_constants
                )
            else:
                serialized_weights = b""

            if config.aot_inductor.package_constants_on_disk_format == "pickle_weights":
                # We need to return a storage key here because the original value tensor might be a clone
                weights_dict = Weights(
                    {
                        graph.allocated_constant_name[name]: (
                            graph.get_original_value_of_constant(name),
                            TensorProperties(graph.constants[name]),
                        )
                        for name in graph.constants
                        if name not in graph.folded_constants
                    }
                )
                generated_files.append(weights_dict)

            consts_size = len(serialized_weights)

            use_external_weights, use_mmap_weights = determine_aoti_mmap_flags(
                consts_size
            )
            if use_external_weights and use_mmap_weights:
                # Should never reach here, just a check for sanity
                raise RuntimeError(
                    "use_external_weights and  use_mmap_weights cannot both be True."
                )

            external_weights_path = None
            if use_external_weights:
                external_weights_filename = f"{wrapper_path_operator.stem}_weights.blob"
                external_weights_path = str(
                    wrapper_path_operator.with_name(external_weights_filename)
                )

            compile_command: dict[str, Any] = {
                "aot_mode": graph.aot_mode,
                "device_type": device_type,
                "use_mmap_weights": use_mmap_weights,
                "use_mmap_weights_external": use_external_weights,
                "use_relative_path": use_relative_path,
                "vec_isa": picked_vec_isa,
            }
            # If we're packaging via CMake, we build the whole code at max optimization.
            wrapper_build_options = CppTorchDeviceOptions(
                compile_only=True,
                min_optimize=not config.aot_inductor.package_cpp_only,
                **compile_command,
            )
            kernel_build_options = CppTorchDeviceOptions(
                compile_only=True,
                **compile_command,
            )

            # potentially, precompile the AOT header for this device
            if config.aot_inductor.precompile_headers and not _IS_WINDOWS:
                header_file = _get_cpp_wrapper_header(
                    device_type, aot_mode=graph.aot_mode
                )
                wrapper_build_options.precompiled_header = _precompile_header(
                    header_file,
                    cpp_command,
                    min_optimize=not config.aot_inductor.package_cpp_only,
                    **compile_command,
                )
                if cpp_prefix := _get_cpp_prefix_header(device_type):
                    kernel_build_options.precompiled_header = _precompile_header(
                        cpp_prefix,
                        cpp_command,
                        **compile_command,
                    )

            wrapper_builder = CppBuilder(
                name=str(wrapper_path_operator.stem),
                sources=wrapper_path,
                output_dir=str(wrapper_path_operator.parent),
                BuildOption=wrapper_build_options,
            )
            wrapper_compile_cmd = wrapper_builder.get_command_line()
            wrapper_o = wrapper_builder.get_target_file_path()

            kernel_builder = CppBuilder(
                name=str(kernel_path_operator.stem),
                sources=kernel_path,
                output_dir=str(wrapper_path_operator.parent),
                BuildOption=kernel_build_options,
            )
            kernel_compile_cmd = kernel_builder.get_command_line()
            kernel_o = kernel_builder.get_target_file_path()

            log.debug("aot wrapper compilation command: %s", wrapper_compile_cmd)
            log.debug("aot kernel compilation command: %s", kernel_compile_cmd)
            if config.aot_inductor.package_cpp_only:
                # Not doing the actual compilation here
                compile_flags = str(
                    wrapper_path_operator.with_name(
                        f"{wrapper_path_operator.stem}_compile_flags.json"
                    )
                )
                wrapper_build_options.save_flags_to_json(compile_flags)
                generated_files.append(compile_flags)
                wrapper_builder.save_compile_cmd_to_cmake(cmake_path, device_type)
                wrapper_builder.save_src_to_cmake(cmake_path, wrapper_path)
                generated_files.append(cmake_path)
            else:
                try:
                    wrapper_builder.build()
                except (exc.CppCompileError, SkipFrame) as e:
                    if " is too big to optimize" in str(e):
                        raise RuntimeError(
                            "Please use torch._inductor.config.aot_inductor.compile_wrapper_opt_level = 'O0' flag."
                        ) from e
                    raise e
                kernel_builder.build()

            if not use_mmap_weights:
                aot_constants = serialized_weights
                magic_number = 0
                if use_external_weights:
                    aot_constants = struct.pack("q", consts_size)
                    assert external_weights_path is not None
                    # For external weights, write weights to separate file and embed minimal placeholder
                    with open(external_weights_path, "wb") as f_weights:
                        f_weights.write(serialized_weights)
                    generated_files.append(external_weights_path)
            else:
                # we'll append weights binary to the end of .so file and mmap it when loading
                magic_number = cast(
                    int, torch.randint(0, torch.iinfo(torch.int64).max, (1,)).item()
                )
                aot_constants = struct.pack("qq", consts_size + 8, magic_number)

            consts_o = _compile_consts(aot_constants, sys.platform)
            custom_obj_idx = 0
            # Note that custom_objs_config.json file is different from the model_constants_config.json file produced
            # in package_sigmoid(). The keys in custom_objs_config.json directly correspond to the arg name in extern
            # nodes json. The key in model_constants_config.json produced by package_sigmoid is the attribute name in the
            # user model code.

            qual_name_to_id = {}  # Map from constant name to its name in constants folder
            for custom_obj_idx, (name, constant) in enumerate(
                graph.torchbind_constants.items()
            ):
                if isinstance(
                    constant, torch._library.fake_class_registry.FakeScriptObject
                ):
                    constant = constant.real_obj
                assert isinstance(constant, torch._C.ScriptObject)
                custom_obj_name = f"{CUSTOM_OBJ_FILENAME_PREFIX}{custom_obj_idx}"

                log.debug("saving script object %s as %s", name, custom_obj_name)

                qual_name_to_id[name] = custom_obj_name
                custom_obj_bytes = torch._C._pickle_save(constant)
                custom_obj_path = os.path.join(
                    wrapper_path_operator.parent, custom_obj_name
                )

                write_atomic(custom_obj_path, custom_obj_bytes, True)
                generated_files.append(custom_obj_path)

            if qual_name_to_id:
                constants_config_json = os.path.join(
                    wrapper_path_operator.parent, "custom_objs_config.json"
                )
                with open(constants_config_json, "w") as f:
                    f.write(json.dumps(qual_name_to_id))
                generated_files.append(constants_config_json)

            cache_cls = {
                "rocm": ROCmCodeCache,
                "cuda": CUDACodeCache,
                "xpu": XPUCodeCache,
            }.get("rocm" if torch.version.hip else device_type, CUDACodeCache)

            gpu_codecache = cache_cls()
            gpu_kernels_o = gpu_codecache.aot_kernels_o.copy()
            # clear the list of aot kernels after each linking
            gpu_codecache.aot_kernels_o.clear()

            if gpu_kernels_o:
                assert not config.aot_inductor.emit_multi_arch_kernel, (
                    "TODO: add emit_multi_arch_kernel support for cutlass kernels"
                )

            cubins_o = []
            asm_files = []
            fatbin_cmds: list[tuple[str, str]] = []
            if not _IS_WINDOWS:
                cubins_to_embed: list[tuple[str, str]] = []
                ld, objcopy = get_ld_and_objcopy(use_relative_path)
                kernels = getattr(V.graph.wrapper_code, "_kernel_name_to_body", {})
                for kernel_name, value in CudaKernelParamCache.cache.items():
                    if kernel_name not in kernels:
                        # It is possible that CudaKernelParamCache contains more Triton kernels
                        # than what the current graph uses
                        continue

                    if asm_file := value["asm"]:
                        asm_files.append(asm_file)

                    cubin_file = value[get_cpp_wrapper_cubin_path_name()]
                    if (
                        config.aot_inductor.emit_multi_arch_kernel
                        and device_type == "cuda"
                    ):
                        if torch.version.hip is None:
                            fatbin_cmds.append((asm_file, cubin_file))

                        else:
                            # ROCm multi-arch: compile LLVM IR to multi-arch bundle
                            from torch._inductor.rocm_multiarch_utils import (
                                compile_multiarch_bundle_from_llvm_ir,
                            )

                            # pyrefly: ignore [unbound-name]
                            if not os.path.exists(asm_file):
                                raise RuntimeError(
                                    f"Multi-arch ROCm compilation requires LLVM IR file, "
                                    # pyrefly: ignore [unbound-name]
                                    f"but {asm_file} not found. "
                                    f"Ensure asm_type='ll' is captured in triton_heuristics.py"
                                )

                            # Compile for multiple archs and bundle them
                            success = compile_multiarch_bundle_from_llvm_ir(
                                # pyrefly: ignore [unbound-name]
                                llvm_ir_path=asm_file,
                                output_bundle_path=cubin_file,
                                target_archs=None,
                            )

                            if not success:
                                raise RuntimeError(
                                    f"Failed to compile multi-arch bundle for kernel {kernel_name}. "
                                    f"Check that ROCm toolchain is available and LLVM IR is valid."
                                )

                            log.info("Created multi-arch bundle: %s", cubin_file)

                    if config.aot_inductor.embed_kernel_binary:
                        cubins_to_embed.append((cubin_file, kernel_name))

                # Compile PTX → fatbin in parallel (each nvcc call is independent).
                # Must complete before cubin embedding below.
                if fatbin_cmds:
                    from concurrent.futures import ThreadPoolExecutor

                    current_arch = cuda_compile_utils._nvcc_arch_as_compile_option()
                    nvcc = cuda_compile_utils._cuda_compiler()

                    def _compile_fatbin(asm_and_cubin: tuple[str, str]) -> None:
                        asm_f, cubin_f = asm_and_cubin
                        cmd = (
                            f"{nvcc} -fatbin {asm_f} -o {cubin_f} "
                            f"-gencode arch=compute_{current_arch},code=compute_{current_arch} "
                            f"-gencode arch=compute_{current_arch},code=sm_{current_arch} "
                        )
                        try:
                            subprocess.run(
                                cmd.split(), capture_output=True, text=True, check=True
                            )
                        except subprocess.CalledProcessError as e:
                            print(
                                f"{cmd} failed with:\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}",
                                file=sys.stderr,
                            )
                            raise

                    with ThreadPoolExecutor() as pool:
                        list(pool.map(_compile_fatbin, fatbin_cmds))

                if cubins_to_embed:
                    # Batch all cubins into a single .o using .incbin assembly.
                    # This replaces N * 3 subprocess calls (ld + 2x objcopy per
                    # cubin) with a single compiler invocation.
                    try:
                        combined_obj = batch_convert_cubins_to_obj(
                            cubins_to_embed,
                            os.path.dirname(output_so),
                            cpp_compiler=get_cpp_compiler(),
                        )
                        cubins_o.append(combined_obj)
                    except subprocess.CalledProcessError:
                        log.warning(
                            "Batched cubin embedding failed, "
                            "falling back to per-cubin objcopy"
                        )
                        for cubin_file, kernel_name in cubins_to_embed:
                            cubins_o.append(
                                convert_cubin_to_obj(
                                    cubin_file, kernel_name, ld, objcopy
                                )
                            )

            output_name, output_dir = get_name_and_dir_from_output_file_path(output_so)
            so_build_options = CppTorchDeviceOptions(
                vec_isa=picked_vec_isa,
                device_type=device_type,
                aot_mode=graph.aot_mode,
                use_relative_path=use_relative_path,
            )

            if gpu_kernels_o and device_type == "xpu":
                so_build_options = CppTorchDeviceOptions(
                    compiler="icpx",
                    vec_isa=picked_vec_isa,
                    device_type=device_type,
                    aot_mode=graph.aot_mode,
                    use_relative_path=use_relative_path,
                    extra_flags=[
                        "-fsycl",
                        "-fsycl-targets=intel_gpu_pvc",
                        "-Xspirv-translator",
                        (
                            "-spirv-ext="
                            "+SPV_INTEL_split_barrier,"
                            "+SPV_INTEL_2d_block_io,"
                            "+SPV_INTEL_subgroup_matrix_multiply_accumulate"
                        ),
                    ],
                )

            obj_srcs = [wrapper_o, kernel_o, consts_o, *gpu_kernels_o, *cubins_o]
            so_builder = CppBuilder(
                name=output_name,
                sources=obj_srcs,
                output_dir=output_dir,
                BuildOption=so_build_options,
            )
            link_cmd = so_builder.get_command_line()
            output_so = so_builder.get_target_file_path()

            log.debug("aot linkage command: %s", link_cmd)

            # Append cmds to the end of codegen-ed wrapper file
            with open(wrapper_path, "a") as f:
                f.write("\n")
                f.write(f"// Compile cmd\n// {wrapper_compile_cmd}\n")
                f.write(f"// Link cmd\n// {link_cmd}\n")

            with open(kernel_path, "a") as f:
                f.write("\n")
                f.write(f"// Compile cmd\n// {kernel_compile_cmd}\n")
                f.write(f"// Link cmd\n// {link_cmd}\n")

            if config.aot_inductor.package_cpp_only:
                linker_flags = str(
                    wrapper_path_operator.with_name(
                        f"{wrapper_path_operator.stem}_linker_flags.json"
                    )
                )
                so_build_options.save_flags_to_json(linker_flags)
                generated_files.append(linker_flags)
                generated_files.append(_LINKER_SCRIPT)

                # If we only want to package the cpp, then we need to save the
                # weights separately into a bin, and we also need to prevent compiling the so
                if use_mmap_weights:
                    weight_file = str(
                        wrapper_path_operator.with_name(
                            f"{wrapper_path_operator.stem}_serialized_weights.bin"
                        )
                    )
                    with open(weight_file, "wb") as f_weights:
                        f_weights.write(serialized_weights)
                        f_weights.write(struct.pack("q", magic_number))

                    generated_files.append(weight_file)
                else:
                    # TODO: unify to always use mmap_weights
                    generated_files.append(consts_o)
                    so_builder.save_src_to_cmake(cmake_path, consts_o)

                # Different CMake strategies for CUDA vs ROCm:
                # - CUDA: Save asm for CMake to recompile (user has nvcc)
                # - ROCm: Link pre-compiled bundle (user may lack dev tools)
                if (
                    config.aot_inductor.emit_multi_arch_kernel
                    and torch.version.hip is None
                ):
                    so_builder.save_kernel_asm_to_cmake(cmake_path, asm_files)
                    generated_files.extend(asm_files)
                else:
                    # ROCm multi-arch + all single-arch: Link pre-compiled objects
                    # Bundle already embedded in .o files - just link into .so
                    obj_srcs = [*gpu_kernels_o, *cubins_o]
                    generated_files.extend(obj_srcs)
                    for obj in obj_srcs:
                        so_builder.save_src_to_cmake(cmake_path, obj)

                so_builder.save_link_cmd_to_cmake(cmake_path)
            else:
                so_builder.build()
                for o_file in obj_srcs:
                    if o_file in gpu_kernels_o:
                        continue
                    # Remove these as they are not needed anymore
                    os.remove(o_file)

                if use_mmap_weights:
                    if config.aot_inductor.cross_target_platform == "windows":
                        raise RuntimeError(
                            "when cross_target_platform is windows, use_mmap_weights should not be true."
                        )

                    def get_page_size() -> int:
                        # Don't use resource.getpagesize() on Windows, as it is a Unix specific package
                        # as seen in https://docs.python.org/2/library/resource.html
                        if _IS_WINDOWS:
                            from ctypes import (
                                byref,
                                Structure,
                                windll,  # pyrefly: ignore [missing-module-attribute]
                            )
                            from ctypes.wintypes import DWORD, LPVOID, WORD

                            class SYSTEM_INFO(Structure):
                                _fields_ = [
                                    ("wProcessorArchitecture", WORD),
                                    ("wReserved", WORD),
                                    ("dwPageSize", DWORD),
                                    ("lpMinimumApplicationAddress", LPVOID),
                                    ("lpMaximumApplicationAddress", LPVOID),
                                    ("dwActiveProcessorMask", DWORD),
                                    ("dwNumberOfProcessors", DWORD),
                                    ("dwProcessorType", DWORD),
                                    ("dwAllocationGranularity", DWORD),
                                    ("wProcessorLevel", WORD),
                                    ("wProcessorRevision", WORD),
                                ]

                            si = SYSTEM_INFO()
                            windll.kernel32.GetSystemInfo(byref(si))
                            sys_page_size = si.dwPageSize
                        else:
                            import resource

                            sys_page_size = resource.getpagesize()

                        return sys_page_size

                    page_size_ = get_page_size()
                    page_size = max(16384, page_size_)

                    with open(output_so, "a+b") as f_so:
                        so_size = f_so.tell()
                        # Page align the weights
                        f_so.write(b" " * (page_size - so_size % page_size))
                        f_so.write(serialized_weights)
                        f_so.write(struct.pack("q", magic_number))

                if config.aot_inductor.package:
                    generated_files.append(output_so)

        if config.trace.provenance_tracking_level != 0:
            kernel_info = torch._inductor.debug.create_kernel_information_json()
            kernel_info_json = os.path.join(
                wrapper_path_operator.parent, "kernel_information.json"
            )
            with open(kernel_info_json, "w") as f:
                f.write(json.dumps(kernel_info, indent=4))
            generated_files.append(kernel_info_json)

        if config.aot_inductor.package:
            # We want to return the directory that contains all the AOTI
            # generated files, not just the so
            # return os.path.split(output_so)[0]
            return generated_files

        return output_so
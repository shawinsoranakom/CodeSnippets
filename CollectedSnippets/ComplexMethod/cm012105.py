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
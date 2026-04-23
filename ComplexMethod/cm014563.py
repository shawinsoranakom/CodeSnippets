def gen_aoti_c_shim_files(
    aoti_fm: FileManager,
    aoti_backends: set[DispatchKey | None],
    native_functions: Sequence[NativeFunction],
    backend_indices: dict[DispatchKey, BackendIndex],
    structured_native_functions: Sequence[NativeFunctionsGroup],
    extra_cuda_headers: str,
    extend_aoti_c_shim: bool,
    update_aoti_c_shim: bool,
) -> None:
    structured_func_group_dict = {}
    for func_group in structured_native_functions:
        for func in func_group.functions():
            if func.structured_delegate is not None:
                structured_func_group_dict[func.structured_delegate] = func_group
                break

    for dispatch_key in aoti_backends:
        # Use aten_shimified_ops for the aten backend, inductor_fallback_ops for others
        fallback_ops_dict = (
            aten_shimified_ops if dispatch_key is None else inductor_fallback_ops
        )
        fallbacks = {}
        for func in native_functions:
            op_name = get_fallback_op_name(func)
            if op_name in fallback_ops_dict:
                fallbacks[op_name] = func
        fallback_native_functions = tuple(
            value for _, value in sorted(fallbacks.items())
        )

        # Use "aten" as the device name when dispatch_key is Generic
        device_name = "aten" if dispatch_key is None else dispatch_key.lower()

        # header files were checked in for ABI-compatibility checking
        header_file_name = f"c_shim_{device_name}.h"
        new_header = gen_aoti_c_shim(
            fallback_native_functions,
            fallback_ops_dict,
            structured_func_group_dict,
            dispatch_key,
            backend_indices,
            header=True,
            extend_aoti_c_shim=extend_aoti_c_shim,
            includes="",
        )
        if update_aoti_c_shim:
            aoti_fm.write(
                header_file_name,
                lambda: new_header,
            )
        else:
            try:
                with open(
                    os.path.join(aoti_fm.install_dir, header_file_name)
                ) as old_file:
                    old_header = old_file.read()

                    if old_header != new_header:
                        diff = "\n".join(
                            difflib.unified_diff(
                                old_header.splitlines(),
                                new_header.splitlines(),
                                fromfile="expected",
                                tofile="actual",
                                lineterm="",
                            )
                        )

                        raise RuntimeError(f"""
The generated AOTInductor C shim header files have unexpectedly changed. This
indicates an AOTInductor fallback operator ABI backward compatibility breakage!!!
Only in a limited number of situations, this is allowed:

1. You added a fallback op to the inductor_fallback_ops list in torchgen/aoti/fallback_ops.py.
If that's the case, run `python torchgen/gen.py --update-aoti-c-shim` to add a new entry to
existing C shim header files.

2. You added a new default argument to an existing fallback op. This is clearly a BC breaking
change in the AOTInductor land. You need to annotate the new default argument in
torchgen/aoti/fallback_ops.py, and then run `python torchgen/gen.py --update-aoti-c-shim` to
update the C shim header files by creating different versions of the fallback op. See
https://github.com/pytorch/pytorch/pull/154848 as an example.

{diff}
                    """)
            except FileNotFoundError:
                print(
                    f"{os.path.join(aoti_fm.install_dir, header_file_name)} not found"
                )

        # cpp files are always generated on-the-fly
        def headers_for_aoti() -> str:
            headers = []
            for func in fallback_native_functions:
                header = get_header_for_aoti(
                    func,
                    structured_func_group_dict,
                    dispatch_key,
                    backend_indices,
                    extend_aoti_c_shim=extend_aoti_c_shim,
                )
                if header is not None:
                    headers.append(header)
            return "\n".join(sorted(set(headers)))

        extra_headers = (
            extra_cuda_headers
            if dispatch_key is not None and is_cuda_dispatch_key(dispatch_key)
            else ""
        )

        aoti_fm.write(
            f"c_shim_{device_name}.cpp",
            lambda: gen_aoti_c_shim(
                fallback_native_functions,
                fallback_ops_dict,
                structured_func_group_dict,
                dispatch_key,
                backend_indices,
                header=False,
                extend_aoti_c_shim=extend_aoti_c_shim,
                includes=headers_for_aoti() + "\n" + extra_headers,
            ),
        )
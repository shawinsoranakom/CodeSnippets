def generate_launch_kernel(self, prefix, wrapper, kernel_var_name, params):
        """
        Generate the GPU kernel launching code.
        This is where all the call args being sorted out and generated.
        If enable_kernel_profile is enabled, all args related information would be packed in this function.
        """
        triton_meta = params["triton_meta"]
        assert len(self.arg_types) == len(params["def_args"]), (
            self.arg_types,
            params["def_args"],
        )
        arg_type_lookup = dict(zip(params["def_args"], self.arg_types))
        # difference between Python and C++ wrapper: C++ wrapper strips out equal_to_1 constants
        call_args = [
            name for name in params["call_args"] if name not in triton_meta["constants"]
        ]
        arg_types = [arg_type_lookup[name] for name in call_args]
        arg_signatures = [triton_meta["signature"][name] for name in call_args]
        num_ctas = params.get("config", {}).get("num_ctas", 1)
        scratch_spaces = {
            name: params[name] * num_ctas
            for name in ["global_scratch", "profile_scratch"]
            if params.get(name, None) is not None
        }
        call_args_str = wrapper.generate_args_decl(
            prefix,
            call_args,
            arg_types,
            arg_signatures,
            scratch_spaces=scratch_spaces,
        )
        prefix.writeline(f"void* kernel_args_[] = {{{call_args_str}}};")
        launch_kernel_args = [
            kernel_var_name,
            "grid_0",
            "grid_1",
            "grid_2",
            str(params["num_warps"]),
            str(params["shared_mem"]),
            "kernel_args_",
            "stream_",
        ]

        enable_kernel_profile = config.cpp.enable_kernel_profile and sys.platform in [
            "linux",
            "win32",
        ]
        if enable_kernel_profile:
            normalized_kernel_name = re.sub(r"[^a-zA-Z0-9_]", "_", f"{kernel_var_name}")
            prefix.writeline("{")
            with prefix.indent():
                prefix.writelines(
                    [
                        f"std::unordered_map<std::string, C10IValueHandle> kwargs_{normalized_kernel_name};",
                        "",
                    ]
                )
                # Add launch args info
                record_launch_kernel_args = [
                    ("grid_0", "grid_0"),
                    ("grid_1", "grid_1"),
                    ("grid_2", "grid_2"),
                    ("num_warps", str(params["num_warps"])),
                    ("shared_mem", str(params["shared_mem"])),
                ]
                for k, v in record_launch_kernel_args:
                    arg_name = f"{normalized_kernel_name}_{k}"
                    prefix.writelines(
                        [
                            f"// Create c10::IValue for {k}",
                            f"C10IValueHandle tmp_{arg_name};",
                            f"aoti_torch_int64_to_ivalue({v}, &tmp_{arg_name});",
                            f"RAIIC10IValueHandle RAII_{arg_name}(tmp_{arg_name});",
                            f'kwargs_{normalized_kernel_name}.emplace("{k}", RAII_{arg_name});',
                        ]
                    )

                # Add input info (This copies the logic from args_decl)
                curr_arg_id = -1
                total_args = []
                ordered_argsname = []

                def write_dummy_scalar_ivalue(arg_name):
                    # We only care about the shape, therefore we create a dummy scalar here.
                    prefix.writelines(
                        [
                            f"// Create c10::IValue for arg_{curr_arg_id}",
                            f"C10IValueHandle tmp_{arg_name};",
                            f"aoti_torch_int64_to_ivalue(0, &tmp_{arg_name});",
                            f"RAIIC10IValueHandle RAII_{arg_name}(tmp_{arg_name});",
                        ]
                    )
                    # pyrefly: ignore [bad-argument-type]
                    total_args.append(f"tmp_{arg_name}")

                def process_args_for_input_shape(arg, arg_type, arg_signature=None):
                    nonlocal curr_arg_id
                    curr_arg_id += 1
                    arg_name = f"{normalized_kernel_name}_arg_{curr_arg_id}"
                    # ignore tma descriptors, as host-side TMA descriptors need
                    # to be passed to the compiled Triton kernel by value
                    if isinstance(
                        arg_type, UnwrapUnspecArg
                    ) and not signature_is_tma_desc(arg_signature):
                        write_dummy_scalar_ivalue(arg_name)
                    elif isinstance(
                        arg_type, torch_dtype
                    ) and not signature_is_tma_desc(arg_signature):
                        # This is an at::Tensor.
                        prefix.writelines(
                            [
                                f"// Create c10::IValue for arg_{curr_arg_id}",
                                f"C10IValueHandle tmp_{arg_name};",
                                f"aoti_torch_tensor_to_ivalue({arg}, &tmp_{arg_name});",
                                f"RAIIC10IValueHandle RAII_{arg_name}(tmp_{arg_name});",
                            ]
                        )
                        # pyrefly: ignore [bad-argument-type]
                        total_args.append(f"tmp_{arg_name}")
                    elif (
                        isinstance(arg_type, type(SymbolicCallArg))
                        and arg_signature is not None
                        and arg_signature in TRITON_SIGNATURE_TO_CPP
                    ) or arg_type in (sympy.Integer, int, sympy.Float, float):
                        write_dummy_scalar_ivalue(arg_name)
                    elif arg_signature and arg_signature.startswith("tensordesc<"):
                        # Skip tma related args
                        pass
                    else:
                        write_dummy_scalar_ivalue(arg_name)

                # Add input name and shape information
                for arg, arg_type, arg_signature in zip_longest(
                    call_args, arg_types, arg_signatures
                ):
                    # pyrefly: ignore [bad-argument-type]
                    ordered_argsname.append(f'"{arg}"')
                    process_args_for_input_shape(arg, arg_type, arg_signature)

                # Add input name into kwargs
                name_var = f"{normalized_kernel_name}_input_names"
                prefix.writelines(
                    [
                        "// Create c10::IValue for input names",
                        f"C10IValueHandle tmp_{name_var};",
                        f"std::vector<const char*> {name_var}({{{', '.join(ordered_argsname)}}});",
                        f"aoti_torch_strlist_to_ivalue({name_var}.data(), {len(ordered_argsname)}, &tmp_{name_var});",
                        f"RAIIC10IValueHandle RAII_{name_var}(tmp_{name_var});",
                        f'kwargs_{normalized_kernel_name}.emplace("Input Args", RAII_{name_var});',
                    ]
                )

                inputs_info_ = f"{normalized_kernel_name}_inputs_info_"
                # We pass in the non-RAII handles, since C10 doesn't automatically free them.
                # The RAII will make sure they get freed when they are out of scope.
                tmp_args = ",".join(total_args)
                prefix.writelines(
                    [
                        "// Aggregate all c10::IValue for inputs",
                        f"std::vector<C10IValueHandle> {inputs_info_}({{{tmp_args}}});",
                    ]
                )

                # Start recording Function
                prefix.writelines(
                    [
                        "",
                        (
                            "torch::aot_inductor::RAIIAtenRecordFunctionHandle "
                            f"record_{normalized_kernel_name}_"
                            f'("{kernel_var_name}", '
                            f"reinterpret_cast<IValueMapHandle>(&kwargs_{normalized_kernel_name}), "
                            f"{inputs_info_});"
                        ),
                        "",
                        f"launchKernel({', '.join(launch_kernel_args)});",
                    ]
                )
            prefix.writeline("}")
        else:
            prefix.writeline(f"launchKernel({', '.join(launch_kernel_args)});")
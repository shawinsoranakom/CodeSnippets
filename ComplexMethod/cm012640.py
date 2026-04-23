def process_args(arg, arg_type, arg_signature=None):
            var_name = f"var_{next(self.arg_var_id)}"
            # ignore tma descriptors, as host-side TMA descriptors need
            # to be passed to the compiled Triton kernel by value
            if isinstance(arg_type, UnwrapUnspecArg) and not signature_is_tma_desc(
                arg_signature
            ):
                self.codegen_tensor_item(
                    arg_type.dtype,
                    arg,
                    var_name,
                    indented_buffer=code,
                )
                new_args.append(f"&{var_name}")
            elif isinstance(arg_type, torch_dtype) and not signature_is_tma_desc(
                arg_signature
            ):
                device_ptr_type = self.device_codegen.cpp_device_ptr()
                code.writeline(
                    maybe_hipify_code_wrapper(
                        f"{device_ptr_type} {var_name} = reinterpret_cast<{device_ptr_type}>({arg}.data_ptr());"
                    )
                )
                new_args.append(f"&{var_name}")
            # For symbolic call arguments, examine the arg signatures from triton meta
            # to explicitly cast to the right type
            # Reason: `auto` can infer unexpected type against kernel input signature.
            elif (
                isinstance(arg_type, type(SymbolicCallArg))
                and arg_signature is not None
                and arg_signature in TRITON_SIGNATURE_TO_CPP
            ):
                code.writeline(
                    f"{TRITON_SIGNATURE_TO_CPP[arg_signature]} {var_name} = {cexpr(arg)};"
                )
                new_args.append(f"&{var_name}")
            elif arg_type in (sympy.Integer, int):
                code.writeline(f"int {var_name} = {cexpr(arg)};")
                new_args.append(f"&{var_name}")
            elif arg_type in (sympy.Float, float):
                # Use signature type if available, otherwise default to float
                cpp_type = TRITON_SIGNATURE_TO_CPP.get(  # pyrefly: ignore[no-matching-overload]
                    arg_signature, "float"
                )
                code.writeline(f"{cpp_type} {var_name} = {cexpr(arg)};")
                new_args.append(f"&{var_name}")
            elif arg_signature and arg_signature.startswith("tensordesc<"):
                new_args.extend(
                    process_tma_stable_arg(arg, arg_type, arg_signature, var_name)
                )
            else:
                code.writeline(f"auto {var_name} = {cexpr(arg)};")
                new_args.append(f"&{var_name}")
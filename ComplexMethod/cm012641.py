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
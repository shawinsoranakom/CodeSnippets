def gen_check(handle_kind, idx, name, tensor):
            # Wrap AtenTensorHandle with ConstantHandle for cleaner utility function access
            self.prefix.writeline(
                f"ConstantHandle {name} = ConstantHandle({handle_kind}[{idx}]);"
            )
            self.codegen_tensor_dtype_var_decl(self.prefix, name)
            expected_dtype_name = DTYPE_TO_ATEN[tensor.dtype]
            dtype_str = str(tensor.dtype).split(".")[-1]
            self.prefix.splice(
                f"""
                    int32_t {name}_expected_dtype = aoti_torch_dtype_{dtype_str}();
                    if ({name}_expected_dtype != {name}_dtype) {{
                        std::stringstream ss;
                        ss << "{handle_kind}[{idx}]: unmatched dtype, "
                           << "expected: " << {name}_expected_dtype << "({expected_dtype_name}), "
                           << "but got: " << {name}_dtype << "\\n";
                        throw std::runtime_error(ss.str());
                    }}
                """
            )
            self.codegen_input_size_var_decl(self.prefix, name)
            for dim_idx, d in enumerate(tensor.get_size()):
                if isinstance(d, (int, sympy.Integer)):
                    self.prefix.splice(
                        f"""
                            if ({d} != {name}_size[{dim_idx}]) {{
                                std::stringstream ss;
                                ss << "{handle_kind}[{idx}]: unmatched dim value at {dim_idx}, "
                                   << "expected: {d}, " << "but got: " << {name}_size[{dim_idx}]
                                   << "\\n";
                                throw std::runtime_error(ss.str());
                            }}
                        """
                    )
                else:
                    from torch.utils._sympy.value_ranges import bound_sympy

                    sym_range = bound_sympy(d, V.graph.sizevars.shape_env.var_to_range)
                    if config.aot_inductor.check_lowerbound and not math.isinf(
                        sym_range.lower
                    ):
                        self.prefix.splice(
                            f"""
                                if ({name}_size[{dim_idx}] < {sym_range.lower}) {{
                                    std::stringstream ss;
                                    ss << "{handle_kind}[{idx}]: dim value is too small at {dim_idx}, "
                                       << "expected it to be >= {sym_range.lower}, " << "but got: "
                                       << {name}_size[{dim_idx}] << "\\n";
                                    throw std::runtime_error(ss.str());
                                }}
                            """
                        )
                    if not math.isinf(sym_range.upper):
                        # Limit upper bound to max C long long value (2^63 - 1)
                        max_long_long = ctypes.c_longlong(2**63 - 1).value
                        upper_bound = min(sym_range.upper, max_long_long)
                        self.prefix.splice(
                            f"""
                                if ({name}_size[{dim_idx}] > {upper_bound}) {{
                                    std::stringstream ss;
                                    ss << "{handle_kind}[{idx}]: dim value is too large at {dim_idx}, "
                                       << "expected to be <= {upper_bound}, " << "but got: "
                                       << {name}_size[{dim_idx}] << "\\n";
                                    throw std::runtime_error(ss.str());
                                }}
                            """
                        )

            self.codegen_input_stride_var_decl(self.prefix, name)
            for stride_idx, s in enumerate(tensor.get_stride()):
                if not isinstance(s, (int, sympy.Integer)):
                    continue
                self.prefix.splice(
                    f"""
                        if ({s} != {name}_stride[{stride_idx}]) {{
                            std::stringstream ss;
                            ss << "{handle_kind}[{idx}]: unmatched stride value at {stride_idx}, "
                               << "expected: {s}, " << "but got: " << {name}_stride[{stride_idx}]
                               << "\\n";
                            throw std::runtime_error(ss.str());
                        }}
                    """
                )

            # check input device type
            if isinstance(tensor, ir.TensorBox):
                tensor_device = tensor.get_device()
                if tensor_device is not None:
                    expected_device_type = DEVICE_TO_INT.get(tensor_device.type)
                    if expected_device_type is not None:
                        self.codegen_input_device_type_var_decl(self.prefix, name)
                        device_type_str = str(tensor_device.type)
                        self.prefix.splice(
                            f"""
                                int32_t {name}_expected_device_type = {expected_device_type};
                                if ({name}_expected_device_type != {name}_device_type) {{
                                    std::stringstream ss;
                                    ss << "{handle_kind}[{idx}]: unmatched device type, "
                                    << "expected: " << {name}_expected_device_type << "{expected_device_type}({device_type_str}), "
                                    << "but got: " << {name}_device_type << "\\n";
                                    throw std::runtime_error(ss.str());
                                }}
                            """
                        )
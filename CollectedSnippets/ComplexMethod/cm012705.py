def generate_py_arg_inner(lines, raw_arg, arg_type):
            def handle_scalar(scalar):
                if isinstance(scalar, int):
                    return f"PyLong_FromLongLong({scalar})"
                if isinstance(scalar, float):
                    return f"PyFloat_FromDouble({self.generate_float_value(scalar)})"
                if isinstance(scalar, bool):
                    return f"PyBool_FromLong({1 if scalar else 0})"
                if isinstance(scalar, complex):
                    real = self.generate_float_value(scalar.real)
                    imag = self.generate_float_value(scalar.imag)
                    return f"PyComplex_FromDoubles({real}, {imag})"
                if isinstance(scalar, SymTypes):
                    scalar_var = cexpr(scalar.node.expr)
                    if isinstance(scalar, torch.SymBool):
                        return f"PyBool_FromLong({scalar_var})"
                    if isinstance(scalar, torch.SymFloat):
                        return f"PyFloat_FromDouble({scalar_var})"
                    return f"PyLong_FromLongLong({scalar_var})"
                raise NotImplementedError(
                    f"scalar {scalar}, {type(scalar)} cannot be handled by handle_scalar"
                )

            if raw_arg is None:
                # Py_None is a singleton, so we have to explicitly incref it here
                lines.append("Py_INCREF(Py_None);\n")
                return "Py_None"
            elif isinstance(arg_type, torch.TensorType):
                # In some cases, scalar arguments may be passed in place of tensors.
                if not hasattr(raw_arg, "codegen_reference"):
                    return handle_scalar(raw_arg)

                # Store AtenTensorHandle as void*.  All Python args are constructed in a
                # nested scope, so this handle will self-destruct after the function
                # call.
                base_handle = self.create_tmp_raii_handle_var_if_needed(
                    raw_arg.codegen_reference(), lines
                )
                return f"PyCapsule_New(reinterpret_cast<void*>({base_handle}.get()), NULL, NULL)"
            elif isinstance(arg_type, torch.OptionalType):
                return generate_py_arg_inner(lines, raw_arg, arg_type.getElementType())
            elif isinstance(arg_type, torch.IntType):
                # int
                return f"PyLong_FromLongLong({raw_arg})"
            elif isinstance(arg_type, torch.SymIntType):
                # SymInt
                expr = (
                    raw_arg.node.expr if isinstance(raw_arg, torch.SymInt) else raw_arg
                )
                return f"PyLong_FromLongLong({cexpr(expr)})"
            elif isinstance(arg_type, torch.FloatType):
                return f"PyFloat_FromDouble({self.generate_float_value(raw_arg)})"
            elif isinstance(arg_type, torch.BoolType):
                return f"PyBool_FromLong({1 if raw_arg else 0})"
            elif isinstance(arg_type, torch.StringType):
                return f'PyUnicode_FromString("{raw_arg}")'
            elif isinstance(arg_type, torch.NumberType):
                # Union[bool, int, float, complex]
                # torch/_prims_common/__init__.py
                return handle_scalar(raw_arg)
            elif isinstance(raw_arg, torch.device):
                device_str, device_index = self.codegen_device(raw_arg).split(", ")
                return f"THPDevice_New(c10::Device(static_cast<c10::DeviceType>({device_str}), {device_index}))"
            elif isinstance(raw_arg, torch.dtype):
                return f"Py_NewRef(torch::getTHPDtype(static_cast<c10::ScalarType>({self.codegen_dtype(raw_arg)})))"
            elif isinstance(raw_arg, torch.layout):
                return f"Py_NewRef(torch::getTHPLayout(static_cast<c10::Layout>({self.codegen_layout(raw_arg)})))"
            elif isinstance(raw_arg, torch.memory_format):
                return (
                    "Py_NewRef(torch::utils::getTHPMemoryFormat(static_cast<c10::MemoryFormat>("
                    f"{self.codegen_memory_format(raw_arg)})))"
                )
            else:
                raise NotImplementedError(
                    f"arg type {arg_type} is not yet supported by custom_op_wrapper"
                )
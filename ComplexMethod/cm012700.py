def val_to_arg_str(self, val, type_=None) -> str:
        if val is None:
            # None needs special care. It either represent nullopt or an empty tensor
            if type_ is None or isinstance(type_, torch.OptionalType):
                if type_ is not None and isinstance(
                    type_.getElementType(),
                    (
                        torch.DeviceObjType,
                        torch.ListType,
                        torch.TupleType,
                    ),
                ):
                    return "nullptr, 0"
                return "nullptr"

            if isinstance(type_, torch.TensorType):
                # create an empty tensor, the equivalent of at::Tensor()
                var_name = f"var_{next(self.arg_var_id)}"
                self.writeline(f"AtenTensorHandle {var_name}_handle;")
                self.writeline(
                    f"AOTI_TORCH_ERROR_CODE_CHECK(aoti_torch_new_uninitialized_tensor(&{var_name}_handle));"
                )
                self.writeline(f"RAIIAtenTensorHandle {var_name}({var_name}_handle);")
                return var_name

            raise AssertionError("Can not map None to a known data type")

        if isinstance(type_, torch.OptionalType):
            element_type = type_.getElementType()
            arg_str = self.val_to_arg_str(val, element_type)
            # Handle optional iterables as a special case.  Utilize the
            # temporary_reference function to avoid saving them off and increasing
            # memory usage.
            if isinstance(element_type, (torch.ListType, torch.TupleType)):
                main_value, aux = arg_str.rsplit(", ", maxsplit=1)
                return f"&temporary_reference({main_value}), {aux}"

            # Handle optional tensors as a special case, as above.
            if isinstance(element_type, torch.TensorType):
                base_handle = self.val_to_arg_str(val, element_type)
                return f"&temporary_reference({base_handle}.get())"

            var_name = f"var_{next(self.arg_var_id)}"
            if isinstance(element_type, torch.DeviceObjType):
                main_value, aux = arg_str.rsplit(", ", maxsplit=1)
                self.writeline(f"auto {var_name} = {main_value};")
                return f"&{var_name}, {aux}"

            self.writeline(
                f"{self.c_type_for_prim_type(val, element_type)} {var_name} = {arg_str};"
            )
            return f"&{var_name}"

        if isinstance(type_, (torch.ListType, torch.TupleType)):
            assert isinstance(val, (list, tuple)), (
                f"{val} does not match with arg type {type_}"
            )
            element_type = type_.getElementType()

            if len(val) == 0:
                # Zero-size array is not supported in the C or C++ standard, so return a
                # nullptr.
                return "nullptr, 0"

            result = [self.val_to_arg_str(x, element_type) for x in val]
            if isinstance(element_type, torch.TensorType):
                result = [f"{t}.get()" for t in result]

            c_type = self.c_type_for_prim_type(val[0], element_type)
            # see the comment in self._generate_temporary_array_pointer for an
            # explanation of why this c_type gets modified
            if isinstance(element_type, torch.OptionalType) and not c_type.startswith(
                "const"
            ):
                c_type = f"const {c_type}"

            # need to pass the array length, because we can't use the std::array member
            # function
            return (
                f"{self._generate_temporary_array_pointer(c_type, result)}, {len(val)}"
            )

        val_is_scalar = isinstance(val, (bool, complex, float, int, *SymTypes))
        if isinstance(type_, torch.TensorType) and val_is_scalar:
            val_str = self.val_to_arg_str_for_prim_type(val, None)
            return self.codegen_scalar_to_tensor(val_str)

        return self.val_to_arg_str_for_prim_type(val, type_)
def return_aten_tensor(self, func: NativeFunction, schema: LazyIrSchema) -> str:
        returns_length = len(schema.returns)
        value_args = schema.filtered_args(values=True, scalars=False)
        value_types_names = [f"{a.name}" for a in value_args if not a.is_wrapped_scalar]
        first_tensor_name = value_types_names[0] if len(value_types_names) > 0 else None
        bridge_str = f"""auto result = {self.create_aten_from_ltc_tensor}(
                {self.create_lazy_tensor(first_tensor_name)}(std::move(node), *common_device));"""

        if returns_length > 1:
            if len(value_types_names) == 0:
                raise AssertionError(
                    "Code below assumes there is at least one tensor arg"
                )
            bridge_str = f"""std::vector<{self.lazy_tensor_ptr}> lazy_tensors;
        for (int i = 0; i < {returns_length}; i++) {{
            lazy_tensors.push_back({self.create_lazy_tensor(first_tensor_name)}({getValueT()}(node, i), *common_device));
        }}
        auto result = {self.tuple_aten_from_ltc_tensors}<{returns_length}>(lazy_tensors);"""

        if schema.name.name.inplace or func.func.is_out_fn():
            if returns_length != 1:
                raise AssertionError(
                    "We assumed there was no such case where an op is an in-place variant "
                    f"and has tuple outputs, but got tuple of len {returns_length}."
                )
            bridge_str = f"""lazy_{first_tensor_name}->SetInPlaceIrValue(node);
        auto& result = {first_tensor_name};"""

        bridge_str += """
        return result;"""
        return bridge_str
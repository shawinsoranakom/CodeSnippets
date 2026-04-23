def codegen_const_args(self, names: list[str] | None = None) -> list[str]:
        if V.graph.cpp_wrapper:
            result = []
            # Aten ops follow the convention that tensor args are before non-tensor args,
            # in which case the following 'len(self.inputs) + i' logic works. But this
            # may not be true for other ops, and if that is the case, caller needs to
            # pass in a list of const arg names for arg_properties lookup.
            name_to_arg_properties = None
            if names and self.arg_properties:
                assert len(self.constant_args) == len(names), (
                    "names passed to codegen_const_args does not match self.constant_args"
                )
                name_to_arg_properties = {
                    arg.get("name"): arg for arg in self.arg_properties
                }

            for i, x in enumerate(self.constant_args):
                if name_to_arg_properties is not None:
                    assert names is not None
                    prop = name_to_arg_properties.get(names[i])
                    type_ = prop.get("type") if prop else None
                else:
                    idx = len(self.inputs) + i
                    type_ = (
                        self.arg_properties[idx].get("type")
                        if self.arg_properties and idx < len(self.arg_properties)
                        else None
                    )
                result.append(V.graph.wrapper_code.val_to_arg_str(x, type_))
            return result
        else:
            return [V.graph.wrapper_code.val_to_arg_str(a) for a in self.constant_args]
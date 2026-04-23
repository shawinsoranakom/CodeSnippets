def collect_arg_kwarg_properties(self) -> None:
        # if self.op_overload is torch._ops.OpOverload, we can use its schema to collect additional
        # information for args and kwargs, e.g. type and default value, to help with the cpp wrapper codegen
        self.arg_properties = (
            [
                {
                    "name": x.name,
                    "type": x.real_type,
                    "default_value": x.default_value,
                }
                for x in self.op_overload._schema.arguments
                if not x.kwarg_only
            ]
            if isinstance(self.op_overload, torch._ops.OpOverload)
            else [{} for i in range(len(self.inputs))]
        )
        self.allarg_properties = (
            {
                x.name: {"type": x.real_type, "default_value": x.default_value}
                for x in self.op_overload._schema.arguments
            }
            if isinstance(self.op_overload, torch._ops.OpOverload)
            else {}
        )
        # FIXME: self.kwargs does not always match kwargs defined in schema, so sometimes
        # ordered_kwargs_for_cpp_kernel is explicitly passed in.
        if isinstance(self.op_overload, torch._ops.OpOverload):
            if not self.ordered_kwargs_for_cpp_kernel:
                self.ordered_kwargs_for_cpp_kernel = [
                    x.name for x in self.op_overload._schema.arguments if x.kwarg_only
                ]
            self.schema_kwargs = [
                x for x in self.op_overload._schema.arguments if x.kwarg_only
            ]
        else:
            self.schema_kwargs = []
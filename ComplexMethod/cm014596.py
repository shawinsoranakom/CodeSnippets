def lazy_tensor_decls(self, func: NativeFunction, schema: LazyIrSchema) -> str:
        value_args = schema.filtered_args(values=True, scalars=False)
        # Generates lazy_{name} variables for LazyTensors wrapping input tensors
        lazy_tensor_decls: list[str] = []
        for arg in value_args:
            if arg.is_wrapped_scalar:
                if isinstance(arg.lazy_type, OptionalCType):
                    lazy_tensor_decls.append(
                        f"""auto node_{arg.name} = {arg.name} ?
                std::make_optional(torch::lazy::LazyGraphExecutor::Get()->
                    GetIrValueForScalarFromCodegen(*{arg.name}, *common_device)):
                ::std::nullopt;"""
                    )
                else:
                    lazy_tensor_decls.append(
                        f"""auto node_{arg.name} = torch::lazy::LazyGraphExecutor::Get()->
                            GetIrValueForScalarFromCodegen({arg.name}, *common_device);"""
                    )
            elif arg.is_symint_or_list:
                continue  # values are extracted in isValueType
            elif isinstance(arg.lazy_type, BaseCType):
                if arg.lazy_type.type is tensorListValueT:
                    lazy_tensor_decls.append(
                        f"auto lazy_{arg.name}_tensorlist = "
                        f"{self.backend_namespace}::{self.get_tensorlist}({arg.name});"
                    )
                else:
                    lazy_tensor_decls.append(
                        f"{self.lazy_tensor_ptr} lazy_{arg.name} = "
                        f"{self.backend_namespace}::{self.get_tensor_or_wrap_number}({arg.name}, *common_device);"
                    )
            elif isinstance(arg.lazy_type, OptionalCType):
                if arg.lazy_type.elem != BaseCType(getValueT()):
                    raise AssertionError(
                        f"Expected OptionalCType elem to be {BaseCType(getValueT())}, "
                        f"got {arg.lazy_type.elem}"
                    )
                # TODO(alanwaketan): Maybe we want to apply GetLtcTensorOrCreateForWrappedNumber here, but hold it
                # until we encounter a real world example.
                lazy_tensor_decls.append(
                    f"{self.lazy_tensor_ptr} lazy_{arg.name} = "
                    f"{self.backend_namespace}::{self.try_get_tensor}({arg.name}.value_or(at::Tensor()));"
                )
            else:
                raise AssertionError(
                    f"TODO not sure if there are other valid types to handle here ({arg.lazy_type})"
                )
        return ("\n        ").join(lazy_tensor_decls)
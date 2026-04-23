def deserialize_input_spec(self, i: InputSpec) -> ep.InputSpec:
        log.debug("[deserialize_input_spec] %s", i)
        if i.type == "user_input":
            return ep.InputSpec(
                kind=ep.InputKind.USER_INPUT,
                arg=self.deserialize_argument_spec(i.user_input.arg),
                target=None,
            )
        elif i.type == "parameter":
            return ep.InputSpec(
                kind=ep.InputKind.PARAMETER,
                arg=ep.TensorArgument(name=i.parameter.arg.name),
                target=i.parameter.parameter_name,
            )
        elif i.type == "buffer":
            return ep.InputSpec(
                kind=ep.InputKind.BUFFER,
                arg=ep.TensorArgument(name=i.buffer.arg.name),
                target=i.buffer.buffer_name,
                persistent=i.buffer.persistent,
            )
        elif i.type == "tensor_constant":
            return ep.InputSpec(
                kind=ep.InputKind.CONSTANT_TENSOR,
                arg=ep.TensorArgument(name=i.tensor_constant.arg.name),
                target=i.tensor_constant.tensor_constant_name,
            )
        elif i.type == "custom_obj":
            return ep.InputSpec(
                kind=ep.InputKind.CUSTOM_OBJ,
                arg=ep.CustomObjArgument(
                    name=i.custom_obj.arg.name, class_fqn=i.custom_obj.arg.class_fqn
                ),
                target=i.custom_obj.custom_obj_name,
            )
        elif i.type == "token":
            return ep.InputSpec(
                kind=ep.InputKind.TOKEN,
                arg=ep.TokenArgument(name=i.token.arg.name),
                target=None,
            )
        elif i.type == "constant_input":
            return ep.InputSpec(
                kind=ep.InputKind.USER_INPUT,
                arg=ep.ConstantArgument(
                    name=i.constant_input.name,
                    value=self.deserialize_constant_input(i.constant_input.value),
                ),
                target=None,
            )
        else:
            raise AssertionError(f"Unknown input spec {i}")
def serialize_input_spec(self, spec: ep.InputSpec) -> InputSpec:
        log.debug("[serialize_input_spec] %s", spec)
        if spec.kind == ep.InputKind.USER_INPUT:
            if isinstance(spec.arg, ep.ConstantArgument):
                if type(spec.arg.value) is int:
                    constant_spec = ConstantValue.create(as_int=spec.arg.value)
                elif type(spec.arg.value) is bool:
                    constant_spec = ConstantValue.create(as_bool=spec.arg.value)
                elif type(spec.arg.value) is str:
                    constant_spec = ConstantValue.create(as_string=spec.arg.value)
                elif type(spec.arg.value) is float:
                    constant_spec = ConstantValue.create(as_float=spec.arg.value)
                elif spec.arg.value is None:
                    constant_spec = ConstantValue.create(as_none=True)
                else:
                    raise SerializeError(
                        f"Unhandled constant input {spec.arg.value} to serialize"
                    )
                return InputSpec.create(
                    constant_input=InputToConstantInputSpec(
                        name=spec.arg.name, value=constant_spec
                    )
                )
            else:
                return InputSpec.create(
                    user_input=UserInputSpec(arg=self.serialize_argument_spec(spec.arg))
                )
        elif spec.kind == ep.InputKind.PARAMETER:
            if spec.target is None:
                raise AssertionError("spec.target should not be None for PARAMETER")
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return InputSpec.create(
                parameter=InputToParameterSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    parameter_name=spec.target,
                )
            )
        elif spec.kind == ep.InputKind.BUFFER:
            if spec.target is None:
                raise AssertionError("spec.target should not be None for BUFFER")
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            if spec.persistent is None:
                raise AssertionError("spec.persistent should not be None for BUFFER")
            return InputSpec.create(
                buffer=InputToBufferSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    buffer_name=spec.target,
                    persistent=spec.persistent,
                )
            )
        elif spec.kind == ep.InputKind.CONSTANT_TENSOR:
            if spec.target is None:
                raise AssertionError(
                    "spec.target should not be None for CONSTANT_TENSOR"
                )
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return InputSpec.create(
                tensor_constant=InputToTensorConstantSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    tensor_constant_name=spec.target,
                )
            )
        elif spec.kind == ep.InputKind.CUSTOM_OBJ:
            if spec.target is None:
                raise AssertionError("spec.target should not be None for CUSTOM_OBJ")
            if not isinstance(spec.arg, ep.CustomObjArgument):
                raise AssertionError(
                    f"expected CustomObjArgument, got {type(spec.arg).__name__}"
                )
            return InputSpec.create(
                custom_obj=InputToCustomObjSpec(
                    arg=CustomObjArgument(
                        name=spec.arg.name, class_fqn=spec.arg.class_fqn
                    ),
                    custom_obj_name=spec.target,
                )
            )
        elif spec.kind == ep.InputKind.TOKEN:
            if not isinstance(spec.arg, ep.TokenArgument):
                raise AssertionError(
                    f"expected TokenArgument, got {type(spec.arg).__name__}"
                )
            return InputSpec.create(
                token=InputTokenSpec(
                    arg=TokenArgument(name=spec.arg.name),
                )
            )
        else:
            raise AssertionError(f"Unknown argument kind: {spec}")
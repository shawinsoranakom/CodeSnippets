def serialize_output_spec(self, spec: ep.OutputSpec) -> OutputSpec:
        log.debug("[serialize_output_spec] %s", spec)
        if spec.kind == ep.OutputKind.USER_OUTPUT:
            return OutputSpec.create(
                user_output=UserOutputSpec(arg=self.serialize_argument_spec(spec.arg))
            )
        elif spec.kind == ep.OutputKind.LOSS_OUTPUT:
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return OutputSpec.create(
                loss_output=LossOutputSpec(arg=TensorArgument(name=spec.arg.name))
            )
        elif spec.kind == ep.OutputKind.BUFFER_MUTATION:
            if spec.target is None:
                raise AssertionError(
                    "spec.target should not be None for BUFFER_MUTATION"
                )
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return OutputSpec.create(
                buffer_mutation=BufferMutationSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    buffer_name=spec.target,
                )
            )
        elif spec.kind == ep.OutputKind.PARAMETER_MUTATION:
            if spec.target is None:
                raise AssertionError(
                    "spec.target should not be None for PARAMETER_MUTATION"
                )
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return OutputSpec.create(
                parameter_mutation=ParameterMutationSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    parameter_name=spec.target,
                )
            )
        elif spec.kind == ep.OutputKind.GRADIENT_TO_PARAMETER:
            if spec.target is None:
                raise AssertionError(
                    "spec.target should not be None for GRADIENT_TO_PARAMETER"
                )
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return OutputSpec.create(
                gradient_to_parameter=GradientToParameterSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    parameter_name=spec.target,
                )
            )
        elif spec.kind == ep.OutputKind.GRADIENT_TO_USER_INPUT:
            if spec.target is None:
                raise AssertionError(
                    "spec.target should not be None for GRADIENT_TO_USER_INPUT"
                )
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return OutputSpec.create(
                gradient_to_user_input=GradientToUserInputSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    user_input_name=spec.target,
                )
            )
        elif spec.kind == ep.OutputKind.USER_INPUT_MUTATION:
            if spec.target is None:
                raise AssertionError(
                    "spec.target should not be None for USER_INPUT_MUTATION"
                )
            if not isinstance(spec.arg, ep.TensorArgument):
                raise AssertionError(
                    f"expected TensorArgument, got {type(spec.arg).__name__}"
                )
            return OutputSpec.create(
                user_input_mutation=UserInputMutationSpec(
                    arg=TensorArgument(name=spec.arg.name),
                    user_input_name=spec.target,
                )
            )
        elif spec.kind == ep.OutputKind.TOKEN:
            if not isinstance(spec.arg, ep.TokenArgument):
                raise AssertionError(
                    f"expected TokenArgument, got {type(spec.arg).__name__}"
                )
            return OutputSpec.create(
                token=OutputTokenSpec(
                    arg=TokenArgument(name=spec.arg.name),
                )
            )
        else:
            raise AssertionError(f"Unknown argument kind: {spec}")
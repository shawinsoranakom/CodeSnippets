def deserialize_output_spec(self, o: OutputSpec) -> ep.OutputSpec:
        log.debug("[deserialize_output_spec] %s", o)
        if o.type == "user_output":
            return ep.OutputSpec(
                kind=ep.OutputKind.USER_OUTPUT,
                arg=self.deserialize_argument_spec(o.user_output.arg),
                target=None,
            )
        elif o.type == "loss_output":
            return ep.OutputSpec(
                kind=ep.OutputKind.LOSS_OUTPUT,
                arg=ep.TensorArgument(name=o.loss_output.arg.name),
                target=None,
            )
        elif o.type == "buffer_mutation":
            return ep.OutputSpec(
                kind=ep.OutputKind.BUFFER_MUTATION,
                arg=ep.TensorArgument(name=o.buffer_mutation.arg.name),
                target=o.buffer_mutation.buffer_name,
            )
        elif o.type == "parameter_mutation":
            return ep.OutputSpec(
                kind=ep.OutputKind.PARAMETER_MUTATION,
                arg=ep.TensorArgument(name=o.parameter_mutation.arg.name),
                target=o.parameter_mutation.parameter_name,
            )
        elif o.type == "gradient_to_parameter":
            return ep.OutputSpec(
                kind=ep.OutputKind.GRADIENT_TO_PARAMETER,
                arg=ep.TensorArgument(name=o.gradient_to_parameter.arg.name),
                target=o.gradient_to_parameter.parameter_name,
            )
        elif o.type == "gradient_to_user_input":
            return ep.OutputSpec(
                kind=ep.OutputKind.GRADIENT_TO_USER_INPUT,
                arg=ep.TensorArgument(name=o.gradient_to_user_input.arg.name),
                target=o.gradient_to_user_input.user_input_name,
            )
        elif o.type == "user_input_mutation":
            return ep.OutputSpec(
                kind=ep.OutputKind.USER_INPUT_MUTATION,
                arg=ep.TensorArgument(name=o.user_input_mutation.arg.name),
                target=o.user_input_mutation.user_input_name,
            )
        elif o.type == "token":
            return ep.OutputSpec(
                kind=ep.OutputKind.TOKEN,
                arg=ep.TokenArgument(name=o.token.arg.name),
                target=None,
            )
        else:
            raise AssertionError(f"Unknown output spec {o}")
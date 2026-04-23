def to_output_spec(idx: int, o: ArgumentSpec) -> OutputSpec:
        if isinstance(o, TokenArgument):
            return OutputSpec(kind=OutputKind.TOKEN, arg=o, target=None)

        if not isinstance(o, TensorArgument):
            return OutputSpec(kind=OutputKind.USER_OUTPUT, arg=o, target=None)
        name = o.name
        if idx < len(buffer_mutations) + len(parameter_mutations) + len(
            user_input_mutations
        ) + len(output_tokens):
            if name in buffer_mutations:
                return OutputSpec(
                    kind=OutputKind.BUFFER_MUTATION,
                    arg=o,
                    target=buffer_mutations[name],  # type: ignore[index]
                )
            elif name in parameter_mutations:
                return OutputSpec(
                    kind=OutputKind.PARAMETER_MUTATION,
                    arg=o,
                    target=parameter_mutations[name],  # type: ignore[index]
                )
            elif name in user_input_mutations:
                return OutputSpec(
                    kind=OutputKind.USER_INPUT_MUTATION,
                    arg=o,
                    target=user_input_mutations[name],  # type: ignore[index]
                )
            else:
                raise AssertionError(f"Unknown tensor mutation kind: {name}")
        else:
            if name in user_outputs:
                return OutputSpec(kind=OutputKind.USER_OUTPUT, arg=o, target=None)

            elif name in grad_params:
                return OutputSpec(
                    kind=OutputKind.GRADIENT_TO_PARAMETER,
                    arg=o,
                    target=grad_params[name],
                )
            elif name in grad_user_inputs:
                return OutputSpec(
                    kind=OutputKind.GRADIENT_TO_USER_INPUT,
                    arg=o,
                    target=grad_user_inputs[name],
                )
            elif name == loss_output:
                return OutputSpec(kind=OutputKind.LOSS_OUTPUT, arg=o, target=None)

            else:
                raise AssertionError(f"Unknown tensor output kind: {name}")
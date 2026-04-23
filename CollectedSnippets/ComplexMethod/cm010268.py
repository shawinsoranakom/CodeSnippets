def backward_signature(self) -> ExportBackwardSignature | None:
        loss_output = None
        gradients_to_parameters: dict[str, str] = {}
        gradients_to_user_inputs: dict[str, str] = {}
        for spec in self.output_specs:
            if spec.kind == OutputKind.LOSS_OUTPUT:
                if loss_output is not None:
                    raise AssertionError("multiple LOSS_OUTPUT specs found")
                if not isinstance(spec.arg, TensorArgument):
                    raise AssertionError(
                        f"expected TensorArgument for LOSS_OUTPUT, got {type(spec.arg)}"
                    )
                loss_output = spec.arg.name
            elif spec.kind == OutputKind.GRADIENT_TO_PARAMETER:
                if not isinstance(spec.target, str):
                    raise AssertionError(
                        f"expected str target for GRADIENT_TO_PARAMETER, got {type(spec.target)}"
                    )
                if not isinstance(spec.arg, TensorArgument):
                    raise AssertionError(
                        f"expected TensorArgument for GRADIENT_TO_PARAMETER, got {type(spec.arg)}"
                    )
                gradients_to_parameters[spec.arg.name] = spec.target
            elif spec.kind == OutputKind.GRADIENT_TO_USER_INPUT:
                if not isinstance(spec.target, str):
                    raise AssertionError(
                        f"expected str target for GRADIENT_TO_USER_INPUT, got {type(spec.target)}"
                    )
                if not isinstance(spec.arg, TensorArgument):
                    raise AssertionError(
                        f"expected TensorArgument for GRADIENT_TO_USER_INPUT, got {type(spec.arg)}"
                    )
                gradients_to_user_inputs[spec.arg.name] = spec.target

        if loss_output is None:
            return None

        return ExportBackwardSignature(
            loss_output=loss_output,
            gradients_to_parameters=gradients_to_parameters,
            gradients_to_user_inputs=gradients_to_user_inputs,
        )
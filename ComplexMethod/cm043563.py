def _generate_argparse_arguments(self, parameters) -> None:
        """Generate the argparse arguments from the function parameters."""
        for param in parameters.values():
            if param.name == "kwargs":
                continue

            param_type, choices = self._get_type_and_choices(param)

            # if the param is a custom type, we need to flatten it
            if inspect.isclass(param_type) and issubclass(param_type, BaseModel):
                # update type hints with the custom type fields
                type_hints = get_type_hints(param_type)
                # prefix the type hints keys with the param name
                type_hints = {
                    f"{param.name}{SEP}{key}": value
                    for key, value in type_hints.items()
                }
                self.type_hints.update(type_hints)
                # create a signature from the custom type
                sig = inspect.signature(param_type)

                # add help to the annotation
                annotated_parameters: list[inspect.Parameter] = []
                for child_param in sig.parameters.values():
                    new_child_param = child_param.replace(
                        name=f"{param.name}{SEP}{child_param.name}",
                        annotation=Annotated[
                            child_param.annotation,
                            OpenBBField(
                                description=param_type.model_json_schema()[
                                    "properties"
                                ][child_param.name].get("description", None)
                            ),
                        ],
                        kind=inspect.Parameter.KEYWORD_ONLY,
                    )
                    annotated_parameters.append(new_child_param)

                # replacing with the annotated parameters
                new_signature = inspect.Signature(
                    parameters=annotated_parameters,
                    return_annotation=sig.return_annotation,
                )
                self._generate_argparse_arguments(new_signature.parameters)

                # the custom type itself should not be added as an argument
                continue

            required = not self._param_is_default(param)

            # Get the appropriate action based on the parameter type
            action = self._get_action_type(param)

            # For boolean parameters with action="store_true", we should not use any choices
            if param_type is bool:
                choices = ()
                action = "store_true"

            argument = ArgparseArgumentModel(
                name=param.name,
                type=param_type,
                dest=param.name,
                default=param.default,
                required=required,
                action=action,
                help=self._escape_help(self._get_argument_custom_help(param)),
                nargs=self._get_nargs(param),
                choices=choices,
            )
            kwargs = argument.model_dump(exclude={"name"}, exclude_none=True)

            if required:
                self._required.add_argument(
                    f"--{argument.name}",
                    **kwargs,
                )
            else:
                self._parser.add_argument(
                    f"--{argument.name}",
                    **kwargs,
                )
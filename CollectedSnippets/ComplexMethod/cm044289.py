def build_command_method(
        cls,
        path: str,
        func: Callable,
        model_name: str | None = None,
        examples: list[Example] | None = None,
    ) -> str:
        """Build the command method."""
        path_parts = [p for p in path.split("/") if p and not p.startswith("{")]
        func_name = path_parts[-1] if path_parts else func.__name__
        sig = signature(func)
        parameter_map = dict(sig.parameters)
        # Get the function source code and extract filter_inputs parameters
        additional_params = {}

        if hasattr(func, "__code__"):
            try:
                func_source = inspect.getsource(func)

                # First, find the filter_inputs block to extract parameter names
                filter_inputs_match = re.search(
                    r"filter_inputs\(\s*(.*?)\s*\)", func_source, re.DOTALL
                )
                if filter_inputs_match:
                    filter_inputs_text = filter_inputs_match.group(1)
                    filter_params = re.findall(r"(\w+)=(\w+)", filter_inputs_text)

                    # Then look for parameter definitions in function body
                    # Find parameters defined with types in comments or actual code
                    param_defs = re.findall(
                        r"(\w+)\s*:\s*(\w+)(?:\s*=\s*([^,\n]+))?", func_source
                    )
                    param_dict = {
                        name: (typ, default) for name, typ, default in param_defs
                    }

                    # Add missing parameters preserving types when available
                    for param_name, param_value in filter_params:
                        if (
                            param_name != param_value
                            and param_value not in parameter_map
                            and param_value not in ["True", "False", "None"]
                        ):
                            # Use type from param_dict if available, otherwise Any
                            if param_value in param_dict:
                                param_type = param_dict[param_value][0]
                                try:
                                    # Try to evaluate the type
                                    annotation = (
                                        eval(  # noqa: S307  # pylint: disable=eval-used
                                            param_type
                                        )
                                    )
                                except (NameError, SyntaxError):
                                    annotation = Any

                                # Get default if available
                                default_str = param_dict[param_value][1]
                                try:
                                    default = (
                                        eval(  # noqa: S307  # pylint: disable=eval-used
                                            default_str
                                        )
                                        if default_str
                                        else None
                                    )
                                except (NameError, SyntaxError):
                                    default = None
                            else:
                                annotation = Any
                                default = None

                            # Add parameter with preserved type/default
                            additional_params[param_value] = Parameter(
                                name=param_value,
                                kind=Parameter.POSITIONAL_OR_KEYWORD,
                                annotation=annotation,
                                default=default,
                            )
            except (OSError, TypeError):
                pass

        # Add missing parameters to parameter_map
        for name, param in additional_params.items():
            if name not in parameter_map:
                parameter_map[name] = param

        formatted_params = cls.format_params(
            path=path, parameter_map=parameter_map, func=func
        )

        has_var_kwargs = any(
            param.kind == Parameter.VAR_KEYWORD for param in formatted_params.values()
        )

        # If not, add **kwargs to formatted_params
        if not has_var_kwargs:
            formatted_params["kwargs"] = Parameter(
                name="kwargs",
                kind=Parameter.VAR_KEYWORD,
                annotation=Any,
                default=Parameter.empty,
            )

        code = cls.build_command_method_signature(
            func_name=func_name,
            formatted_params=formatted_params,
            return_type=sig.return_annotation,
            path=path,
            model_name=model_name,
        )
        code += cls.build_command_method_doc(
            path=path,
            func=func,
            formatted_params=formatted_params,
            model_name=model_name,
            examples=examples,
        )

        code += cls.build_command_method_body(
            path=path, func=func, formatted_params=formatted_params
        )

        return code
def validate_inputs(self, args_names: list[dict[str, str]], args: Any, kwargs: Any):
        """Validate the inputs."""
        if len(args) > 0 and len(args) != len(args_names):
            msg = "Number of positional arguments does not match the number of inputs. Pass keyword arguments instead."
            raise ToolException(msg)

        if len(args) == len(args_names):
            kwargs = {arg_name["arg_name"]: arg_value for arg_name, arg_value in zip(args_names, args, strict=True)}

        missing_args = [arg["arg_name"] for arg in args_names if arg["arg_name"] not in kwargs]
        if missing_args:
            msg = f"Missing required arguments: {', '.join(missing_args)}"
            raise ToolException(msg)

        return kwargs
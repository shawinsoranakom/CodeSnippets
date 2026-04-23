def _extract_tool_info(self, tool):
        """
        Helper function to extract the signature and description of a tool's methods.
        """
        tool_info = {"signature": tool.__class__.__name__, "methods": []}
        if tool.__class__.__name__ == "Browser":
            methods = []
            for name in dir(tool):
                if "driver" in name:
                    continue  # Skip methods containing 'driver' in their name
                attr = getattr(tool, name)
                if (
                    callable(attr)
                    and not name.startswith("_")
                    and not hasattr(attr, "__wrapped__")
                    and not isinstance(attr, property)
                ):
                    # Construct the method signature manually
                    param_str = ", ".join(
                        param
                        for param in attr.__code__.co_varnames[
                            : attr.__code__.co_argcount
                        ]
                    )
                    full_signature = f"computer.{tool.__class__.__name__.lower()}.{name}({param_str})"
                    # Get the method description
                    method_description = attr.__doc__ or ""
                    # Append the method details
                    tool_info["methods"].append(
                        {
                            "signature": full_signature,
                            "description": method_description.strip(),
                        }
                    )
            return tool_info

        for name, method in inspect.getmembers(tool, predicate=inspect.ismethod):
            # Check if the method should be ignored based on its decorator
            if not name.startswith("_") and not hasattr(method, "__wrapped__"):
                # Get the method signature
                method_signature = inspect.signature(method)
                # Construct the signature string without *args and **kwargs
                param_str = ", ".join(
                    f"{param.name}"
                    if param.default == param.empty
                    else f"{param.name}={param.default!r}"
                    for param in method_signature.parameters.values()
                    if param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
                )
                full_signature = (
                    f"computer.{tool.__class__.__name__.lower()}.{name}({param_str})"
                )
                # Get the method description
                method_description = method.__doc__ or ""
                # Append the method details
                tool_info["methods"].append(
                    {
                        "signature": full_signature,
                        "description": method_description.strip(),
                    }
                )
        return tool_info
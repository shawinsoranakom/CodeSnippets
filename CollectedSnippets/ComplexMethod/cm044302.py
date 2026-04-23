def _extract_return_type(func: Callable) -> str | dict:
        """Extract return type information from function."""
        return_annotation = inspect.signature(func).return_annotation

        # If no return annotation, or return annotation is inspect.Signature.empty
        if return_annotation is inspect.Signature.empty:
            return {"type": "Any"}

        # Use get_type_hints to resolve TypeVars
        hints = get_type_hints(func)
        return_annotation = hints.get("return", return_annotation)

        # Check if the return type is an OBBject
        type_str = str(return_annotation)
        if "OBBject" in type_str or (
            hasattr(return_annotation, "__name__")
            and "OBBject" in return_annotation.__name__
        ):
            # Extract the model name from docstring or type annotation
            result_type = "Any"  # Default fallback

            # Try to extract from type annotation first (more reliable)
            origin = get_origin(return_annotation)
            if origin is not None:
                args = get_args(return_annotation)
                if len(args) > 1:
                    # For OBBject[T, SomeType], results type is SomeType
                    result_type = args[1].__name__
                else:
                    # For OBBject[SomeType]
                    inner_type = args[0] if args else None
                    if inner_type is not None:
                        # Handle container types like list[Model]
                        inner_origin = get_origin(inner_type)
                        if inner_origin is not None:
                            inner_args = get_args(inner_type)
                            if inner_args:
                                container_type = inner_origin
                                model_type = inner_args[0]
                                result_type = (
                                    f"{container_type.__name__}[{model_type.__name__}]"
                                )
                        elif hasattr(inner_type, "__name__"):
                            result_type = inner_type.__name__
                            # Resolve TypeVar bound if available
                            if (
                                hasattr(inner_type, "__bound__")
                                and inner_type.__bound__
                            ):
                                result_type = inner_type.__bound__.__name__
                        elif hasattr(inner_type, "_name") and inner_type._name:
                            result_type = inner_type._name
            else:
                # Fallback: parse from type_str if get_origin fails
                match = re.search(r"OBBject\[.*?\]\[(.*?)\]", type_str)
                if match:
                    result_type = match.group(1)
                # Check for OBBject_ModelName pattern
                elif "OBBject_" in type_str:
                    result_type = type_str.split("OBBject_")[1].split("'")[0]

            # If not found, try to extract from docstring
            if result_type == "list[Data]":
                docstring = inspect.getdoc(func) or ""
                if "Returns" in docstring:
                    returns_section = docstring.split("Returns")[1].split("\n\n")[0]
                    # Look for model name in docstring
                    patterns = [
                        r"OBBject\[(.*?)\]",  # OBBject[Model]
                        r"results : ([\w\d_]+)",  # results : Model
                        r"Returns\s+-------\s+(\w+)",  # Direct return type
                    ]

                    for pattern in patterns:
                        model_match = re.search(pattern, returns_section)
                        if model_match:
                            result_type = model_match.group(1)
                            break

            # Ensure result_type doesn't already have a container type
            if "[" in result_type and "]" not in result_type:
                result_type += "]"  # Add missing closing bracket
            result_type = ReferenceGenerator._clean_string_values(result_type)
            # Return the standard OBBject structure with correct result type
            return {
                "OBBject": [
                    {
                        "name": "results",
                        "type": result_type,
                        "description": "Serializable results.",
                    },
                    {
                        "name": "provider",
                        "type": "Optional[str]",
                        "description": "Provider name.",
                    },
                    {
                        "name": "warnings",
                        "type": "Optional[list[Warning_]]",
                        "description": "List of warnings.",
                    },
                    {
                        "name": "chart",
                        "type": "Optional[Chart]",
                        "description": "Chart object.",
                    },
                    {
                        "name": "extra",
                        "type": "dict[str, Any]",
                        "description": "Extra info.",
                    },
                ]
            }

        # Clean up return type string
        type_str = (
            type_str.replace("<class '", "")
            .replace("'>", "")
            .replace("typing.", "")
            .replace("NoneType", "None")
            .replace("inspect._empty", "Any")
        )

        # Basic types handling
        basic_types = ["int", "str", "dict", "bool", "float", "None", "Any"]
        if type_str.lower() in [t.lower() for t in basic_types]:
            return type_str.lower()

        # Check for container types with square brackets
        container_match = re.search(r"(\w+)\[(.*?)\]", type_str)
        if container_match:
            container_type = container_match.group(1)
            inner_type = container_match.group(2)

            inner_type_name = (
                inner_type.split(".")[-1] if "." in inner_type else inner_type
            )

            return f"{container_type}[{inner_type_name}]"

        model_name = (
            type_str.rsplit(".", maxsplit=1)[-1] if "." in type_str else type_str
        )

        return model_name
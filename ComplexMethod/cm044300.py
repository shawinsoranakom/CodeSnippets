def _get_function_signature_info(func: Callable) -> list[dict[str, Any]]:
        """Extract parameter information directly from function signature."""
        params_info = []
        sig = signature(func)

        for name, param in sig.parameters.items():
            # Skip 'self' and context parameters
            if name in ["self", "cc"]:
                continue

            # Skip parameters with dependency injections through annotations
            if isinstance(param.annotation, _AnnotatedAlias) and any(
                hasattr(meta, "dependency") for meta in param.annotation.__metadata__
            ):
                continue

            # Skip parameters with Depends in default values
            if param.default is not Parameter.empty:
                default_str = str(param.default)
                if "Depends" in default_str:
                    continue

            param_type = param.annotation
            is_optional = (
                param.default is not Parameter.empty
            )  # Parameter is optional if it has a default value
            description = ""
            choices = None
            default = param.default if param.default is not Parameter.empty else None
            json_extra: dict = {}

            # Check if type is optional
            if (
                hasattr(param_type, "__origin__")
                and param_type.__origin__ is Union
                and (type(None) in param_type.__args__ or None in param_type.__args__)
            ):
                # Check if None or NoneType is in the union
                is_optional = True
                # Extract the actual type (excluding None)
                non_none_args = [
                    arg
                    for arg in param_type.__args__
                    if arg is not type(None) and arg is not None
                ]
                if len(non_none_args) == 1:
                    param_type = non_none_args[0]

            if isinstance(param_type, _AnnotatedAlias):
                base_type = param_type.__args__[0]
                for meta in param_type.__metadata__:
                    if hasattr(meta, "description"):
                        description = meta.description
                    if hasattr(meta, "choices"):
                        choices = meta.choices
                    if hasattr(meta, "default"):
                        default = meta.default
                    if hasattr(meta, "json_schema_extra"):
                        json_extra = meta.json_schema_extra

                # Set the actual type to the base type
                param_type = base_type

            # Handle Query objects passed as parameters or default values.
            if str(default.__class__).endswith("Query'>") or "Query" in str(
                default.__class__
            ):
                param_type = (
                    param_type.annotation
                    if hasattr(param_type, "annotation")
                    else str(param_type)
                )
                description = default.description  # type: ignore
                json_extra = default.json_schema_extra  # type: ignore
                has_default = hasattr(default, "default") and default.default not in [  # type: ignore
                    Parameter.empty,
                    PydanticUndefined,
                    Ellipsis,
                ]
                is_optional = has_default or (
                    hasattr(default, "is_required") and default.is_required is False  # type: ignore
                )
                default = (
                    default.default  # type: ignore
                    if default.default not in [Parameter.empty, PydanticUndefined, Ellipsis]  # type: ignore
                    else None
                )

            # Convert type to string representation
            type_str = str(param_type)
            # Clean up type string
            type_str = (
                type_str.replace("<class '", "")
                .replace("'>", "")
                .replace("typing.", "")
                .replace("NoneType", "None")
                .replace("inspect._empty", "Any")
            )
            params_info.append(
                {
                    "name": name,
                    "type": type_str,
                    "description": ReferenceGenerator._clean_string_values(description),
                    "default": (
                        None
                        if default in (PydanticUndefined, Parameter.empty, Ellipsis)
                        else ReferenceGenerator._clean_string_values(default)
                    ),
                    "optional": is_optional,
                    "choices": choices or json_extra.pop("choices", []),
                    "multiple_items_allowed": json_extra.pop(
                        "multiple_items_allowed", False
                    ),
                    "json_schema_extra": json_extra or {},
                }
            )

        return params_info
def get_function_hint_type_list(cls, route) -> list[type]:
        """Get the hint type list from the function."""

        no_validate = (getattr(route, "openapi_extra", None) or {}).get("no_validate")

        func = route.endpoint
        sig = signature(func)
        if no_validate is True:
            route.response_model = None

        parameter_map = sig.parameters
        return_type = (
            sig.return_annotation if not no_validate else route.response_model or Any
        )

        hint_type_list: list = []

        for parameter in parameter_map.values():
            hint_type_list.append(parameter.annotation)

            # Extract dependencies from Annotated metadata
            if isinstance(parameter.annotation, _AnnotatedAlias):
                for meta in parameter.annotation.__metadata__:
                    # Check if this is a Depends object
                    if hasattr(meta, "dependency"):
                        # Add the dependency function to hint_type_list
                        hint_type_list.append(meta.dependency)

        if return_type:
            hint_type = (
                get_args(get_type_hints(return_type)["results"])[0]
                if hasattr(return_type, "__class__")
                and hasattr(return_type.__class__, "__name__")
                and "OBBject" in getattr(return_type.__class__, "__name__", "")
                else return_type
            )
            hint_type_list.append(hint_type)

        hint_type_list = cls.filter_hint_type_list(hint_type_list)

        return hint_type_list
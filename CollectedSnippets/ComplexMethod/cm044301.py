def get_paths(  # noqa: PLR0912
        cls, route_map: dict[str, BaseRoute]
    ) -> dict[str, dict[str, Any]]:
        """Get path reference data.

        The reference data is a dictionary containing the description, parameters,
        returns and examples for each endpoint. This is currently useful for
        automating the creation of the website documentation files.

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary containing the description, parameters, returns and
            examples for each endpoint.
        """
        reference: dict[str, dict] = {}

        for path, route in route_map.items():
            # Initialize the provider parameter fields as an empty dictionary
            provider_parameter_fields = {"type": ""}
            # Initialize the reference fields as empty dictionaries
            reference[path] = {field: {} for field in cls.REFERENCE_FIELDS}
            # Route method is used to distinguish between GET and POST methods
            route_method = getattr(route, "methods", None)
            # Route endpoint is the callable function
            route_func = getattr(route, "endpoint", lambda: None)
            # Attribute contains the model and examples info for the endpoint
            openapi_extra = getattr(route, "openapi_extra", {}) or {}
            # Standard model is used as the key for the ProviderInterface Map dictionary
            standard_model = openapi_extra.get("model", "")
            # Add endpoint model for GET methods
            reference[path]["model"] = standard_model
            # Add endpoint deprecation details
            reference[path]["deprecated"] = {
                "flag": MethodDefinition.is_deprecated_function(path),
                "message": MethodDefinition.get_deprecation_message(path),
            }
            # Add endpoint examples
            examples = openapi_extra.get("examples", [])
            reference[path]["examples"] = cls._get_endpoint_examples(
                path,
                route_func,
                examples,  # type: ignore
            )
            validate_output = not openapi_extra.get("no_validate", None)
            model_map = cls.pi.map.get(standard_model, {})
            # Exclude transient keys that were only needed above
            reference[path]["openapi_extra"] = {
                k: v
                for k, v in openapi_extra.items()
                if k not in ("examples", "no_validate")
            }

            # Extract return type information for all endpoints
            return_info = cls._extract_return_type(route_func)

            # Add data for the endpoints having a standard model
            if route_method and model_map:
                reference[path]["description"] = getattr(
                    route, "description", "No description available."
                )
                for provider in model_map:
                    if provider == "openbb":
                        # openbb provider is always present hence its the standard field
                        reference[path]["parameters"]["standard"] = (
                            cls._get_provider_field_params(
                                standard_model, "QueryParams"
                            )
                        )
                        # Add `provider` parameter fields to the openbb provider
                        provider_parameter_fields = cls._get_provider_parameter_info(
                            standard_model
                        )

                        # Add endpoint data fields for standard provider
                        reference[path]["data"]["standard"] = (
                            cls._get_provider_field_params(standard_model, "Data")
                        )
                        continue

                    # Adds provider specific parameter fields to the reference
                    reference[path]["parameters"][provider] = (
                        cls._get_provider_field_params(
                            standard_model, "QueryParams", provider
                        )
                    )

                    # Adds provider specific data fields to the reference
                    reference[path]["data"][provider] = cls._get_provider_field_params(
                        standard_model, "Data", provider
                    )

                    # Remove choices from standard parameters if they exist in provider-specific parameters
                    provider_param_names = {
                        p["name"] for p in reference[path]["parameters"][provider]
                    }

                    for i, param in enumerate(
                        reference[path]["parameters"]["standard"]
                    ):
                        param_name = param.get("name")
                        if (
                            param_name in provider_param_names
                            and param.get("choices") is not None
                        ):
                            # This parameter has a provider-specific version, so remove choices from standard
                            reference[path]["parameters"]["standard"][i][
                                "choices"
                            ] = None

                # Add endpoint returns data
                if validate_output is False:
                    reference[path]["returns"]["Any"] = {
                        "description": "Unvalidated results object.",
                    }
                else:
                    providers = provider_parameter_fields["type"]
                    if isinstance(return_info, dict) and "OBBject" in return_info:
                        results_field = next(
                            (
                                f
                                for f in return_info["OBBject"]
                                if f["name"] == "results"
                            ),
                            None,
                        )
                        if results_field:
                            results_type = results_field["type"]
                            if results_type == "Any":
                                results_type = f"list[{standard_model}]"
                            reference[path]["returns"]["OBBject"] = (
                                cls._get_obbject_returns_fields(results_type, providers)
                            )
            # Add data for the endpoints without a standard model (data processing endpoints)
            else:
                results_type = "Any"
                openapi_extra = (
                    getattr(
                        route_func, "openapi_extra", getattr(route, "openapi_extra", {})
                    )
                    or {}
                )

                model_name = openapi_extra.get("model", "") or ""
                if isinstance(return_info, dict) and "OBBject" in return_info:
                    results_field = next(
                        (f for f in return_info["OBBject"] if f["name"] == "results"),
                        None,
                    )
                    if results_field:
                        results_type = results_field["type"]
                        # Extract model name from types like list[Model] or Model
                        if "[" in results_type and "]" in results_type:
                            inner_type = results_type.split("[")[1].split("]")[0]
                            extracted_model = (
                                inner_type.split(".")[-1]
                                if "." in inner_type
                                else inner_type
                            )
                            model_name = model_name or extracted_model
                        else:
                            extracted_model = (
                                results_type.split(".")[-1]
                                if "." in results_type
                                else results_type
                            )
                            model_name = model_name or extracted_model

                formatted_params = MethodDefinition.format_params(
                    path=path,
                    parameter_map=dict(signature(route_func).parameters),
                    func=route_func,
                )

                docstring = DocstringGenerator.generate(
                    path=path,
                    func=route_func,
                    formatted_params=formatted_params,
                    model_name=model_name,
                    examples=examples,
                )
                if not docstring:
                    continue

                description = docstring.split("Parameters")[0].strip()
                reference[path]["description"] = re.sub(" +", " ", description)

                # Extract parameters directly from formatted_params
                reference[path]["parameters"]["standard"] = []
                for param in formatted_params.values():
                    if param.name == "kwargs":
                        continue
                    annotation = param.annotation
                    if isinstance(annotation, _AnnotatedAlias):
                        type_str = DocstringGenerator.get_field_type(
                            annotation.__args__[0], False, "website"
                        )
                        # Search all metadata items for a description
                        description = ""
                        for meta in annotation.__metadata__:
                            desc = getattr(meta, "description", "")
                            if desc:
                                description = desc
                                break
                    else:
                        type_str = DocstringGenerator.get_field_type(
                            annotation, False, "website"
                        )
                        description = ""
                    reference[path]["parameters"]["standard"].append(
                        {
                            "name": param.name,
                            "type": type_str,
                            "description": description,
                            "default": (
                                param.default
                                if param.default != Parameter.empty
                                else None
                            ),
                            "optional": param.default != Parameter.empty,
                        }
                    )
                # Set returns based on return_info
                if isinstance(return_info, dict) and "OBBject" in return_info:
                    results_field = next(
                        (f for f in return_info["OBBject"] if f["name"] == "results"),
                        None,
                    )
                    if results_field:
                        results_type = results_field["type"]
                        reference[path]["returns"]["OBBject"] = (
                            cls._get_obbject_returns_fields(results_type, "str")
                        )

                # Extract data fields from the model class if results_type is not "Any"
                if results_type != "Any":
                    # Try to extract model name
                    if "[" in results_type:
                        if results_type.startswith("list["):
                            extracted_model_name = results_type[5:-1]
                        else:
                            extracted_model_name = results_type.split("[")[1].split(
                                "]"
                            )[0]
                    else:
                        extracted_model_name = results_type

                    # Try to get the model class from the function's module
                    try:
                        module = sys.modules[route_func.__module__]
                        model_class = getattr(module, extracted_model_name, None)
                        if model_class and hasattr(type(model_class), "model_fields"):
                            # Set data to the fields
                            reference[path]["data"]["standard"] = []
                            for field_name, field in getattr(
                                type(model_class), "model_fields", {}
                            ).items():
                                field_type = DocstringGenerator.get_field_type(
                                    field.annotation, field.is_required(), "website"
                                )
                                json_extra = getattr(field, "json_schema_extra", {})
                                reference[path]["data"]["standard"].append(
                                    {
                                        "name": field_name,
                                        "type": field_type,
                                        "description": getattr(
                                            field, "description", ""
                                        ),
                                        "default": (
                                            None
                                            if field.default is PydanticUndefined
                                            else field.default
                                        ),
                                        "optional": not field.is_required(),
                                        "json_schema_extra": json_extra or {},
                                    }
                                )
                    except (KeyError, AttributeError):
                        pass

        return reference
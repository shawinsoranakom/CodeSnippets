def generate(  # pylint: disable=too-many-positional-arguments  # noqa: PLR0912
        cls,
        path: str,
        func: Callable,
        formatted_params: OrderedDict[str, Parameter],
        model_name: str | None = None,
        examples: list[Example] | None = None,
    ) -> str | None:
        """Generate the docstring for the function."""
        doc = inspect.getdoc(func) or ""
        param_types = {}
        sections = SystemService().system_settings.python_settings.docstring_sections
        max_length = (
            SystemService().system_settings.python_settings.docstring_max_length
        )
        # Parameters explicit in the function signature
        explicit_params = dict(formatted_params)
        explicit_params.pop("extra_params", None)
        # Map of parameter names to types
        param_types = {k: v.annotation for k, v in explicit_params.items()}

        if model_name:
            params = cls.provider_interface.params.get(model_name, {})
            return_schema = cls.provider_interface.return_schema.get(model_name, None)
            if params and return_schema:
                # Parameters passed as **kwargs
                kwarg_params = params["extra"].__dataclass_fields__
                param_types.update({k: v.type for k, v in kwarg_params.items()})
                # Format the annotation to hide the metadata, tags, etc.
                annotation = func.__annotations__.get("return")
                model_fields = getattr(annotation, "model_fields", {})
                results_type = (
                    cls._get_repr(
                        cls._get_generic_types(
                            model_fields["results"].annotation,  # type: ignore[union-attr,arg-type]
                            [],
                        ),
                        model_name,
                    )
                    if isclass(annotation)
                    and issubclass(annotation, OBBject)  # type: ignore[arg-type]
                    and "results" in model_fields
                    else model_name
                )
                doc = cls.generate_model_docstring(
                    model_name=model_name,
                    summary=func.__doc__ or "",
                    explicit_params=explicit_params,
                    kwarg_params=kwarg_params,
                    returns=getattr(return_schema, "model_fields", {}),
                    results_type=results_type,
                    sections=sections,
                )
                doc += "\n"

                if "examples" in sections:
                    doc += cls.build_examples(
                        path.replace("/", "."),
                        param_types,
                        examples,
                    )
                    doc += "\n"
        else:
            primitive_types = {
                "int",
                "float",
                "str",
                "bool",
                "list",
                "dict",
                "tuple",
                "set",
            }
            type_name: str = ""
            sections = (
                SystemService().system_settings.python_settings.docstring_sections
            )
            doc_has_parameters = bool(
                re.search(r"^\s*Parameters\s*\n[-=~`]{3,}", doc, re.MULTILINE)
            )
            doc_has_returns = bool(
                re.search(r"^\s*Returns\s*\n[-=~`]{3,}", doc, re.MULTILINE)
            )
            doc_has_examples = bool(
                re.search(r"^\s*Examples\s*\n[-=~`]{3,}", doc, re.MULTILINE)
            )
            result_doc = doc.strip("\n")

            if result_doc:
                result_doc += "\n\n"

            if (
                formatted_params
                and "parameters" in sections
                and not doc_has_parameters
                and [p for p_name, p in formatted_params.items() if p_name != "kwargs"]
            ):
                if result_doc and not result_doc.endswith("\n\n"):
                    result_doc = result_doc.rstrip("\n") + "\n\n"
                elif not result_doc:
                    result_doc = "\n\n"

                param_section = "Parameters\n----------\n"

                for param_name, param in formatted_params.items():
                    if param_name == "kwargs":
                        continue

                    annotation = getattr(param, "_annotation", None)

                    if isinstance(annotation, _AnnotatedAlias):
                        p_type = annotation.__args__[0]  # type: ignore
                        metadata = getattr(annotation, "__metadata__", [])
                        description = (
                            getattr(metadata[0], "description", "") if metadata else ""
                        )
                    else:
                        p_type = annotation
                        description = ""

                    type_str = cls.get_field_type(
                        p_type, param.default is Parameter.empty
                    )
                    param_section += f"{create_indent(1)}{param_name} : {type_str}\n"

                    if description and description.strip() != '""':
                        param_section += f"{create_indent(2)}{description}\n"

                result_doc += param_section + "\n"

            if "returns" in sections and not doc_has_returns:
                if result_doc and not result_doc.endswith("\n\n"):
                    result_doc = result_doc.rstrip("\n") + "\n\n"

                returns_section = "Returns\n-------\n"
                sig = inspect.signature(func)
                return_annotation = sig.return_annotation

                if (
                    return_annotation
                    and return_annotation
                    != inspect._empty  # pylint: disable=protected-access
                ):
                    if hasattr(return_annotation, "__name__"):
                        type_name = return_annotation.__name__
                    else:
                        type_name = str(return_annotation)

                    type_name = (
                        type_name.replace("typing.", "")
                        .replace("typing_extensions.", "")
                        .replace("<class '", "")
                        .replace("'>", "")
                        .replace("OBBject[T]", "OBBject")
                    )

                    returns_section += f"{type_name}\n"
                    is_primitive = type_name.lower() in primitive_types

                    if not is_primitive:
                        try:
                            if hasattr(type(return_annotation), "model_fields"):
                                fields = getattr(
                                    type(return_annotation), "model_fields", {}
                                )

                                for field_name, field in fields.items():
                                    field_type = cls.get_field_type(
                                        field.annotation, field.is_required
                                    )
                                    description = (
                                        field.description.replace('"', "'")
                                        if field.description
                                        else ""
                                    )

                                    if type_name.startswith("OBBject"):
                                        if field_name != "id":
                                            returns_section += "\n"

                                        returns_section += f"{create_indent(2)}{field_name.strip()} : {field_type}"
                                    else:
                                        returns_section += f"{create_indent(2)}{field_name} : {field_type}\n"
                                    if description:
                                        returns_section += (
                                            f"\n{create_indent(3)}{description}"
                                        )

                        except (AttributeError, TypeError):
                            pass
                else:
                    returns_section += "Any\n"

                result_doc += returns_section + "\n"
                result_doc = result_doc.replace("\n    ", f"\n{create_indent(2)}")

            doc = result_doc.rstrip()

            # Check response type for OBBject types to extract inner type
            # Expand the docstring with the schema fields like in model-based commands
            if type_name and "OBBject" in type_name:
                type_str = str(return_annotation).replace("[T]", "")
                match = re.search(r"OBBject\[(.*)\]", type_str)
                inner = match.group(1) if match else ""
                # Extract from list[Type] or dict[str, Type]
                type_match = re.search(r"\[([^\[\]]+)\]$", inner)
                extracted_type = type_match.group(1) if type_match else inner

                if extracted_type and extracted_type.lower() not in primitive_types:
                    route_map = PathHandler.build_route_map()
                    paths = ReferenceGenerator.get_paths(route_map)
                    route_path = paths.get(path, {}).get("data", {}).get("standard", [])

                    if route_path:
                        if doc and not doc.endswith("\n\n"):
                            doc += "\n\n"
                        doc += f"{extracted_type}\n"
                        doc += f"{'-' * len(extracted_type)}\n"

                        for field in route_path:
                            field_name = field.get("name", "")
                            field_type = field.get("type", "Any")
                            field_description = field.get("description", "")
                            doc += f"{create_indent(2)}{field_name} : {field_type}\n"
                            if field_description:
                                doc += f"{create_indent(3)}{field_description}\n"

                        doc += "\n"

            if "examples" in sections and not doc_has_examples:
                if doc and not doc.endswith("\n\n"):
                    doc += "\n\n"
                doc += cls.build_examples(
                    path.replace("/", "."),
                    param_types,
                    examples,
                )
                doc += "\n"

        if (  # pylint: disable=chained-comparison
            max_length and len(doc) > max_length and max_length > 3
        ):
            doc = doc[: max_length - 3] + "..."
        return doc
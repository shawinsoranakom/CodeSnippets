def build_command_method_body(
        path: str,
        func: Callable,
        formatted_params: OrderedDict[str, Parameter] | None = None,
    ):
        """Build the command method implementation."""
        if formatted_params is None:
            formatted_params = OrderedDict()

        sig = signature(func)
        parameter_map = dict(sig.parameters)
        parameter_map.pop("cc", None)

        # Extract dependencies without disrupting other code paths
        dependency_calls: list = []
        dependency_names = set()

        seen_router_dependency_funcs: set = set()
        for dependency in PathHandler.get_router_dependencies(path):
            dependency_func = getattr(dependency, "dependency", None)
            if (
                callable(dependency_func)
                and dependency_func not in seen_router_dependency_funcs
                and MethodDefinition._is_safe_dependency(dependency_func)
            ):
                dependency_identifier = MethodDefinition._dependency_identifier(
                    dependency_func
                )
                dependency_calls.append(
                    f"        {dependency_identifier} = {dependency_func.__name__}()"
                )
                dependency_calls.append(
                    f"        kwargs['{dependency_identifier}'] = {dependency_identifier}"
                )
                seen_router_dependency_funcs.add(dependency_func)

        # Process dependencies
        for name, param in parameter_map.items():
            if isinstance(param.annotation, _AnnotatedAlias):
                for meta in param.annotation.__metadata__:
                    if hasattr(meta, "dependency") and meta.dependency is not None:
                        dependency_func = meta.dependency

                        if not MethodDefinition._is_safe_dependency(dependency_func):
                            continue

                        func_name = dependency_func.__name__
                        dependency_calls.append(f"        {name} = {func_name}()")
                        dependency_names.add(name)

        code = ""

        if dependency_calls:
            code += "\n".join(dependency_calls) + "\n\n"

        if CHARTING_INSTALLED and path.replace("/", "_")[1:] in Charting.functions():
            parameter_map["chart"] = Parameter(
                name="chart",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=bool,
                default=False,
            )

        if MethodDefinition.is_deprecated_function(path):
            deprecation_message = MethodDefinition.get_deprecation_message(path)
            code += "        simplefilter('always', DeprecationWarning)\n"
            code += f"""        warn("{deprecation_message}", category=DeprecationWarning, stacklevel=2)\n\n"""

        info = {}

        code += "        return self._run(\n"
        code += f"""            "{path}",\n"""
        code += "            **filter_inputs(\n"

        # Check if we already have a kwargs parameter (VAR_KEYWORD) in formatted_params
        has_kwargs = any(
            param.kind == Parameter.VAR_KEYWORD for param in formatted_params.values()
        )
        has_extra_params = False

        for name, param in parameter_map.items():
            if name == "extra_params":
                has_extra_params = True
                fields = (
                    param.annotation.__args__[0].__dataclass_fields__
                    if hasattr(param.annotation, "__args__")
                    else param.annotation
                )
                values = {k: k for k in fields}
                for k in values:
                    if extra := MethodDefinition.get_extra(fields[k]):
                        info[k] = extra
                code += f"                {name}=kwargs,\n"
            elif name == "provider_choices":
                field = param.annotation.__args__[0].__dataclass_fields__["provider"]
                available = field.type.__args__
                cmd = path.strip("/").replace("/", ".")
                code += "                provider_choices={\n"
                code += '                    "provider": self._get_provider(\n'
                code += "                        provider,\n"
                code += f'                        "{cmd}",\n'
                code += f"                        {available},\n"
                code += "                    )\n"
                code += "                },\n"
            elif MethodDefinition.is_annotated_dc(param.annotation):
                fields = param.annotation.__args__[0].__dataclass_fields__
                values = {k: k for k in fields}
                code += f"                {name}={{\n"
                for k, v in values.items():
                    code += f'                    "{k}": {v},\n'
                    if extra := MethodDefinition.get_extra(fields[k]):
                        info[k] = extra
                code += "                },\n"
            elif (
                isinstance(param.annotation, _AnnotatedAlias)
                and (
                    hasattr(type(param.annotation.__args__[0]), "model_fields")
                    or hasattr(param.annotation.__args__[0], "__pydantic_fields__")
                )
                and not MethodDefinition.is_data_processing_function(path)
            ):
                has_depends = any(
                    hasattr(meta, "dependency")
                    for meta in param.annotation.__metadata__
                )
                if not has_depends:
                    model = param.annotation.__args__[0]
                    fields = getattr(
                        type(model),
                        "model_fields",
                        getattr(model, "__pydantic_fields__", {}),
                    )
                    values = {k: k for k in fields}
                    code += f"                {name}={{\n"
                    for k, v in values.items():
                        code += f'                    "{k}": {v},\n'
                    code += "                },\n"
                else:
                    code += f"                {name}={name},\n"
            elif name != "kwargs":
                code += f"                {name}={name},\n"

        if info:
            code += f"                info={info},\n"

        if MethodDefinition.is_data_processing_function(path):
            code += "                data_processing=True,\n"

        # Add kwargs parameter
        if has_kwargs and not has_extra_params:
            code += "                **kwargs,\n"

        code += "            )\n"
        code += "        )\n"

        return code
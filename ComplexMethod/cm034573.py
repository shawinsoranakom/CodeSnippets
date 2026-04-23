def get_parameters(cls, as_json: bool = False) -> dict[str, Parameter]:
        params = {name: parameter for name, parameter in signature(
            cls.create_async_generator if issubclass(cls, AsyncGeneratorProvider) else
            cls.create_async if issubclass(cls, AsyncProvider) else
            cls.create_completion
        ).parameters.items() if name in SAFE_PARAMETERS
            and (name != "stream" or cls.supports_stream)}
        if as_json:
            def get_type_as_var(annotation: type, key: str, default):
                if key in PARAMETER_EXAMPLES:
                    if key == "messages" and not cls.supports_system_message:
                        return [PARAMETER_EXAMPLES[key][-1]]
                    return PARAMETER_EXAMPLES[key]
                if isinstance(annotation, type):
                    if issubclass(annotation, int):
                        return 0
                    elif issubclass(annotation, float):
                        return 0.0
                    elif issubclass(annotation, bool):
                        return False
                    elif issubclass(annotation, str):
                        return ""
                    elif issubclass(annotation, dict):
                        return {}
                    elif issubclass(annotation, list):
                        return []
                    elif issubclass(annotation, BaseConversation):
                        return {}
                    elif issubclass(annotation, NoneType):
                        return {}
                elif annotation is None:
                    return None
                elif annotation == "str" or annotation == "list[str]":
                    return default
                elif isinstance(annotation, _GenericAlias):
                    if annotation.__origin__ is Optional:
                        return get_type_as_var(annotation.__args__[0])
                else:
                    return str(annotation)
            return { name: (
                param.default
                if isinstance(param, Parameter) and param.default is not Parameter.empty and param.default is not None
                else get_type_as_var(param.annotation, name, param.default) if isinstance(param, Parameter) else param
            ) for name, param in {
                **BASIC_PARAMETERS,
                **params,
                **{"provider": cls.__name__, "model": getattr(cls, "default_model", ""), "stream": cls.supports_stream},
            }.items()}
        return params
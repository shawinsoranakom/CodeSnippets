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
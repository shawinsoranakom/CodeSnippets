def _dependency_identifier(dependency_func: Callable) -> str:
        try:
            return_annotation = signature(dependency_func).return_annotation
        except (ValueError, TypeError):
            return_annotation = inspect._empty

        class_name = ""
        if return_annotation not in (inspect._empty, None):
            if isinstance(return_annotation, str):
                class_name = return_annotation.rsplit(".", maxsplit=1)[-1]
            elif isclass(return_annotation):
                class_name = return_annotation.__name__

        if not class_name and isclass(dependency_func):
            class_name = dependency_func.__name__

        if not class_name:
            func_name = dependency_func.__name__
            class_name = (
                func_name[4:]
                if func_name.startswith("get_") and len(func_name) > 4
                else func_name
            )

        identifier = MethodDefinition._snake_case(class_name)
        return identifier or MethodDefinition._snake_case(dependency_func.__name__)
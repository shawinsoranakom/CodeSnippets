def _has_request_bound_annotation(annotation: Any) -> bool:
        if annotation is Parameter.empty:
            return False

        origin = get_origin(annotation)
        if origin is Annotated:
            args = get_args(annotation)
            if not args:
                return False
            return MethodDefinition._has_request_bound_annotation(args[0])

        origin = get_origin(annotation)
        if origin is Union or (UnionType is not None and origin is UnionType):
            args = get_args(annotation) or getattr(annotation, "__args__", ())
            return any(
                MethodDefinition._has_request_bound_annotation(arg) for arg in args
            )

        if isinstance(annotation, str):
            normalized = annotation.lower().strip()
            normalized = normalized.replace("typing.", "")
            normalized = normalized.replace("builtins.", "")
            normalized = normalized.split("[", 1)[0]
            return normalized in MethodDefinition.REQUEST_BOUND_ANNOTATION_NAMES

        if isinstance(annotation, type):
            return annotation in MethodDefinition.REQUEST_BOUND_PARAM_TYPES

        return annotation in MethodDefinition.REQUEST_BOUND_PARAM_TYPES
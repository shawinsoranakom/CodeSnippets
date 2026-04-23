def _is_none_like_return(annotation: Any) -> bool:
        if annotation in (None, type(None)):
            return True
        if annotation is inspect._empty:
            return False
        if isinstance(annotation, str):
            normalized = annotation.lower().strip()
            normalized = normalized.replace("typing.", "")
            normalized = normalized.replace("builtins.", "")
            normalized = normalized.split("[", 1)[0]
            return normalized in {"none", "nonetype"}

        origin = get_origin(annotation)
        if origin is Union or (UnionType is not None and origin is UnionType):
            args = get_args(annotation) or getattr(annotation, "__args__", ())
            if not args:
                return True
            return all(MethodDefinition._is_none_like_return(arg) for arg in args)

        return False
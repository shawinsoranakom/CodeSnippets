def _unwrap_optional_annotation(annotation: Any) -> Any:
        """Remove a single None branch from a union annotation."""
        if isinstance(annotation, UnionType):
            non_none = [item for item in get_args(annotation) if item is not type(None)]
            if len(non_none) == 1:
                return non_none[0]
            return annotation

        if get_origin(annotation) is None:
            return annotation

        non_none = [item for item in get_args(annotation) if item is not type(None)]
        if len(non_none) == 1 and len(non_none) != len(get_args(annotation)):
            return non_none[0]
        return annotation
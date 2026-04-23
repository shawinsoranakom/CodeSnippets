def _extract_type_name(annotation) -> str | None:
    """
    Extract the type name from an AST annotation node.
    Handles: TypeName, Optional[TypeName], Union[TypeName, ...], list[TypeName], etc.
    Returns the base type name if found, or None.
    """
    if isinstance(annotation, ast.Name):
        # Simple type: TypeName
        return annotation.id
    elif isinstance(annotation, ast.Subscript):
        # Generic type: Optional[TypeName], list[TypeName], etc.
        # Try to extract from the subscript value
        if isinstance(annotation.value, ast.Name):
            # If it's Optional, Union, list, etc., look at the slice
            if isinstance(annotation.slice, ast.Name):
                return annotation.slice.id
            elif isinstance(annotation.slice, ast.Tuple):
                # Union[TypeName, None] - take first element
                if annotation.slice.elts and isinstance(annotation.slice.elts[0], ast.Name):
                    return annotation.slice.elts[0].id
    return None
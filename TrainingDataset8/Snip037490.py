def _ensure_serialization(o: object) -> Union[str, List[Any]]:
    """repr function for json.dumps default arg, which tries to serialize sets as lists"""
    if isinstance(o, set):
        return list(o)
    return repr(o)
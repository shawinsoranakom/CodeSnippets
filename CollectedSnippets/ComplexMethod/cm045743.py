def _serialize_item_for_mssql(value: Any) -> Any:
    """Convert a Pathway/Python value to a form pymssql can bind, matching what
    the Pathway MSSQL writer (bind_value in mssql.rs) produces."""
    if value is None:
        return None
    if isinstance(value, pw.PyObjectWrapper):
        return api.serialize(value)  # type: ignore[arg-type]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str, bytes)):
        return value
    if isinstance(value, pw.Pointer):
        return str(value)
    if isinstance(value, pw.Json):
        return json.dumps(value.value)
    if isinstance(value, pd.Timedelta):
        return value.value // 1000  # nanoseconds → microseconds (bind_value uses µs)
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, np.ndarray):
        return json.dumps(
            {"shape": list(value.shape), "elements": value.flatten().tolist()}
        )
    if isinstance(value, (list, tuple)):
        return json.dumps(_to_json_serializable(value))
    return value
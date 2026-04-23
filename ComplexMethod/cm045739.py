def normalize_input(value):
        if isinstance(value, pw.Pointer):
            return str(value)
        if isinstance(value, pw.Json):
            return value.value
        if isinstance(value, pd.Timestamp):
            result = value.to_pydatetime()
            if not timezone_supported:
                result = result.replace(tzinfo=None)
            return result
        if isinstance(value, pd.Timedelta):
            return value.value // timestamp_precision
        if isinstance(value, np.ndarray):
            return normalize_input(value.tolist())
        if hasattr(value, "_create_with_serializer"):
            return value.value
        if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, dict)):
            return [normalize_input(v) for v in value]
        return value
def convert_value(v):
        if v is None:
            return "Not available"
        if isinstance(v, str):
            v_stripped = v.strip().lower()
            if v_stripped in {"null", "nan", "infinity", "-infinity"}:
                return "Not available"
        if isinstance(v, float):
            try:
                if math.isnan(v):
                    return "Not available"
            except Exception as e:  # noqa: BLE001
                logger.aexception(f"Error converting value {v} to float: {e}")

        if hasattr(v, "isnat") and getattr(v, "isnat", False):
            return "Not available"
        return v
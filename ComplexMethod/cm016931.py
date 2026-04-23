def _parse_metadata_json(cls, v):
        if v is None or isinstance(v, dict):
            return v or {}
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return {}
            try:
                parsed = json.loads(s)
            except Exception as e:
                raise ValueError(f"user_metadata must be JSON: {e}") from e
            if not isinstance(parsed, dict):
                raise ValueError("user_metadata must be a JSON object")
            return parsed
        return {}
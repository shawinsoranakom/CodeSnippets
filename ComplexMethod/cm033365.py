def default_for_type(t):
        """Return default value for the given schema type."""
        if t == "file":
            return []
        if t == "object":
            return {}
        if t == "boolean":
            return False
        if t == "number":
            return 0
        if t == "string":
            return ""
        if t and t.startswith("array"):
            return []
        if t == "null":
            return None
        return None
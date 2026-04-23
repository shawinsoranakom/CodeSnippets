def from_serializable_dict(data: Any) -> Any:
    """
    Recursively convert a serializable dictionary back to an object instance.
    """
    if data is None:
        return None

    # Handle basic types
    if isinstance(data, (str, int, float, bool)):
        return data

    # Handle typed data
    if isinstance(data, dict) and "type" in data:
        # Handle plain dictionaries
        if data["type"] == "dict":
            return {k: from_serializable_dict(v) for k, v in data["value"].items()}

        # Import from crawl4ai for class instances
        import crawl4ai
        cls = getattr(crawl4ai, data["type"])

        # Handle Enum
        if issubclass(cls, Enum):
            return cls(data["params"])

        # Handle class instances
        constructor_args = {
            k: from_serializable_dict(v) for k, v in data["params"].items()
        }
        return cls(**constructor_args)

    # Handle lists
    if isinstance(data, list):
        return [from_serializable_dict(item) for item in data]

    # Handle raw dictionaries (legacy support)
    if isinstance(data, dict):
        return {k: from_serializable_dict(v) for k, v in data.items()}

    return data
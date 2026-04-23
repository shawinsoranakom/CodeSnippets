def from_serializable_dict(data: Any) -> Any:
    """
    Recursively convert a serializable dictionary back to an object instance.
    """
    if data is None:
        return None

    # Handle basic types
    if isinstance(data, (str, int, float, bool)):
        return data

    # Handle typed data.
    # Only enter the typed-object path for dicts that match the shapes produced
    # by to_serializable_dict(): {"type": "<ClassName>", "params": {...}} or
    # {"type": "dict", "value": {...}}.  Plain business dicts that happen to
    # carry a "type" key (e.g. JSON-Schema fragments, JsonCss field specs like
    # {"type": "text", "name": "..."}) have neither "params" nor "value" and
    # must fall through to the raw-dict path below so they are passed as data.
    if (
        isinstance(data, dict)
        and "type" in data
        and ("params" in data or (data["type"] == "dict" and "value" in data))
    ):
        # Handle plain dictionaries
        if data["type"] == "dict" and "value" in data:
            return {k: from_serializable_dict(v) for k, v in data["value"].items()}

        # Security: only allow known-safe types to be deserialized.
        # Unknown types (e.g. logging.Logger serialized by older clients) are
        # silently dropped (returned as None) instead of crashing the request.
        type_name = data["type"]
        if type_name not in ALLOWED_DESERIALIZE_TYPES:
            return None

        cls = None
        module_paths = ["crawl4ai"]
        for module_path in module_paths:
            try:
                mod = importlib.import_module(module_path)
                if hasattr(mod, type_name):
                    cls = getattr(mod, type_name)
                    break
            except (ImportError, AttributeError):
                continue

        if cls is not None:
            # Handle Enum
            if issubclass(cls, Enum):
                return cls(data["params"])

            if "params" in data:
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
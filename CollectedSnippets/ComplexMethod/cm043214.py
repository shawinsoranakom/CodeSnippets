def to_serializable_dict(obj: Any, ignore_default_value : bool = False):
    """
    Recursively convert an object to a serializable dictionary using {type, params} structure
    for complex objects.
    """
    if obj is None:
        return None

    # Handle basic types
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # Handle Enum
    if isinstance(obj, Enum):
        return {"type": obj.__class__.__name__, "params": obj.value}

    # Handle datetime objects
    if hasattr(obj, "isoformat"):
        return obj.isoformat()

    # Handle lists, tuples, and sets, and basically any iterable
    if isinstance(obj, (list, tuple, set)) or hasattr(obj, '__iter__') and not isinstance(obj, dict):
        return [to_serializable_dict(item) for item in obj]

    # Handle frozensets, which are not iterable
    if isinstance(obj, frozenset):
        return [to_serializable_dict(item) for item in list(obj)]

    # Handle dictionaries - preserve them as-is
    if isinstance(obj, dict):
        return {
            "type": "dict",  # Mark as plain dictionary
            "value": {str(k): to_serializable_dict(v) for k, v in obj.items()},
        }

    _type = obj.__class__.__name__

    # Handle class instances
    if hasattr(obj, "__class__"):
        # Skip types that cannot be deserialized (e.g. logging.Logger, callables).
        # Only serialize objects whose type is in ALLOWED_DESERIALIZE_TYPES so that
        # from_serializable_dict can reconstruct them on the other side.
        if _type not in ALLOWED_DESERIALIZE_TYPES:
            return None

        # Get constructor signature
        sig = inspect.signature(obj.__class__.__init__)
        params = sig.parameters

        # Get current values
        current_values = {}
        for name, param in params.items():
            if name == "self":
                continue

            value = getattr(obj, name, param.default)

            # Only include if different from default, considering empty values
            if not (is_empty_value(value) and is_empty_value(param.default)):
                if value != param.default and not ignore_default_value:
                    current_values[name] = to_serializable_dict(value)

        # Don't serialize private __slots__ - they're internal implementation details
        # not constructor parameters. This was causing URLPatternFilter to fail
        # because _simple_suffixes was being serialized as 'simple_suffixes'
        # if hasattr(obj, '__slots__'):
        #     for slot in obj.__slots__:
        #         if slot.startswith('_'):  # Handle private slots
        #             attr_name = slot[1:]  # Remove leading '_'
        #             value = getattr(obj, slot, None)
        #             if value is not None:
        #                 current_values[attr_name] = to_serializable_dict(value)

        return {
            "type": obj.__class__.__name__,
            "params": current_values
        }

    return str(obj)
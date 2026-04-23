def make_hashable(obj: Any) -> Any:
        """Recursively convert an object to a hashable representation."""
        if isinstance(obj, dict):
            # Sort dict items to ensure consistent ordering
            return (
                "__dict__",
                tuple(sorted((k, make_hashable(v)) for k, v in obj.items())),
            )
        elif isinstance(obj, (list, tuple)):
            return ("__list__", tuple(make_hashable(item) for item in obj))
        elif isinstance(obj, set):
            return ("__set__", tuple(sorted(make_hashable(item) for item in obj)))
        elif hasattr(obj, "__dict__"):
            # Handle objects with __dict__ attribute
            return ("__obj__", obj.__class__.__name__, make_hashable(obj.__dict__))
        else:
            # For basic hashable types (str, int, bool, None, etc.)
            try:
                hash(obj)
                return obj
            except TypeError:
                # Fallback: convert to string representation
                return ("__str__", str(obj))
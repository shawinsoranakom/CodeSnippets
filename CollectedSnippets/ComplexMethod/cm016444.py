def _format_type_annotation(
        cls, annotation, type_tracker: Optional[TypeTracker] = None
    ) -> str:
        """Convert a type annotation to its string representation for stub files."""
        if (
            annotation is inspect.Parameter.empty
            or annotation is inspect.Signature.empty
        ):
            return "Any"

        # Handle None type
        if annotation is type(None):
            return "None"

        # Track the type if we have a tracker
        if type_tracker:
            type_tracker.track_type(annotation)

        # Try using typing.get_origin/get_args for Python 3.8+
        try:
            origin = get_origin(annotation)
            args = get_args(annotation)

            if origin is not None:
                # Track the origin type
                if type_tracker:
                    type_tracker.track_type(origin)

                # Get the origin name
                origin_name = getattr(origin, "__name__", str(origin))
                if "." in origin_name:
                    origin_name = origin_name.split(".")[-1]

                # Special handling for types.UnionType (Python 3.10+ pipe operator)
                # Convert to old-style Union for compatibility
                if str(origin) == "<class 'types.UnionType'>" or origin_name == "UnionType":
                    origin_name = "Union"

                # Format arguments recursively
                if args:
                    formatted_args = []
                    for arg in args:
                        # Track each type in the union
                        if type_tracker:
                            type_tracker.track_type(arg)
                        formatted_args.append(cls._format_type_annotation(arg, type_tracker))
                    return f"{origin_name}[{', '.join(formatted_args)}]"
                else:
                    return origin_name
        except (AttributeError, TypeError):
            # Fallback for older Python versions or non-generic types
            pass

        # Handle generic types the old way for compatibility
        if hasattr(annotation, "__origin__") and hasattr(annotation, "__args__"):
            origin = annotation.__origin__
            origin_name = (
                origin.__name__
                if hasattr(origin, "__name__")
                else str(origin).split("'")[1]
            )

            # Format each type argument
            args = []
            for arg in annotation.__args__:
                args.append(cls._format_type_annotation(arg, type_tracker))

            return f"{origin_name}[{', '.join(args)}]"

        # Handle regular types with __name__
        if hasattr(annotation, "__name__"):
            return annotation.__name__

        # Handle special module types (like types from typing module)
        if hasattr(annotation, "__module__") and hasattr(annotation, "__qualname__"):
            # For types like typing.Literal, typing.TypedDict, etc.
            return annotation.__qualname__

        # Last resort: string conversion with cleanup
        type_str = str(annotation)

        # Clean up common patterns more robustly
        if type_str.startswith("<class '") and type_str.endswith("'>"):
            type_str = type_str[8:-2]  # Remove "<class '" and "'>"

        # Remove module prefixes for common modules
        for prefix in ["typing.", "builtins.", "types."]:
            if type_str.startswith(prefix):
                type_str = type_str[len(prefix) :]

        # Handle special cases
        if type_str in ("_empty", "inspect._empty"):
            return "None"

        # Fix NoneType (this should rarely be needed now)
        if type_str == "NoneType":
            return "None"

        return type_str
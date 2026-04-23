def str_to_enum(cls, value):
        """
        Convert a string, enum instance, or None to the appropriate enum member.

        Args:
            value: Can be an enum instance of this class, a string, or None

        Returns:
            Enum member of this class

        Raises:
            ValueError: If the value cannot be converted to a valid enum member
        """
        # Already an enum instance of this class
        if isinstance(value, cls):
            return value

        # None maps to NONE member if it exists
        if value is None:
            if hasattr(cls, "NONE"):
                return cls.NONE
            raise ValueError(f"{cls.__name__} does not have a NONE member to map None to")

        # String conversion (case-insensitive)
        if isinstance(value, str):
            value_lower = value.lower()

            # Try to match against enum values
            for member in cls:
                # Handle members with None values
                if member.value is None:
                    if value_lower == "none":
                        return member
                # Handle members with string values
                elif isinstance(member.value, str) and member.value.lower() == value_lower:
                    return member

            # Build helpful error message with valid values
            valid_values = []
            for member in cls:
                if member.value is None:
                    valid_values.append("none")
                elif isinstance(member.value, str):
                    valid_values.append(member.value)

            raise ValueError(f"Invalid {cls.__name__} string: '{value}'. " f"Valid values are: {valid_values}")

        raise ValueError(
            f"Cannot convert type {type(value).__name__} to {cls.__name__} enum. "
            f"Expected string, None, or {cls.__name__} instance."
        )
def format_first_error(self) -> str:
        """Return a sanitized first validation error message.

        Missing-field errors keep explicit field names for UX.
        Model-level ``value_error`` messages (from model validators) are
        passed through after stripping the pydantic "Value error, " prefix,
        since those contain intentional business-logic messages.
        All other errors avoid echoing raw validator text.
        """
        errors = self.error.errors()
        if not errors:
            return "Invalid payload."

        first_error = errors[0]
        loc = first_error.get("loc") or ()
        loc_path = ".".join(str(part) for part in loc if part != "__root__")

        error_type = first_error.get("type")

        if error_type == "missing" and loc_path:
            return f"Missing required field '{loc_path}'."
        if error_type in {"extra_forbidden", "unexpected_keyword_argument"} and loc_path:
            return f"Invalid field '{loc_path}'. Please remove it."
        if loc_path:
            return f"Invalid value for field '{loc_path}'."
        # Model-level validator errors (empty loc) contain intentional
        # business-logic messages; expose them after stripping the
        # pydantic "Value error, " prefix.
        if first_error.get("type") == "value_error":
            msg = first_error.get("msg", "")
            clean = msg.removeprefix("Value error, ")
            if clean:
                return clean
        return "Invalid payload."
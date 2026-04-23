def get_display_value(self, value: Any) -> str:
        """Get display-friendly representation of a value."""
        if value is None:
            return "[not set]"
        if self.field_type == "secret":
            secret_val = (
                value.get_secret_value() if isinstance(value, SecretStr) else str(value)
            )
            if not secret_val:
                return "[not set]"
            # Mask all but first 3 and last 4 characters
            if len(secret_val) > 10:
                return f"{secret_val[:3]}...{secret_val[-4:]}"
            return "***"
        if self.field_type == "bool":
            return "true" if value else "false"
        return str(value)
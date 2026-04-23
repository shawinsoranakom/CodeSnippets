def serialization_alias(self) -> str | None:
        sa = self.field_info.serialization_alias
        return sa or None
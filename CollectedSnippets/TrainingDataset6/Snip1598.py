def validation_alias(self) -> str | None:
        va = self.field_info.validation_alias
        if isinstance(va, str) and va:
            return va
        return None
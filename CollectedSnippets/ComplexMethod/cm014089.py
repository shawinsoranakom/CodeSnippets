def _flatten_type_spec(self, value: Any) -> list[type] | None:
        if isinstance(value, type):
            return [value]
        if isinstance(value, tuple):
            collected: list[type] = []
            for entry in value:
                flat = self._flatten_type_spec(entry)
                if flat is None:
                    return None
                collected.extend(flat)
            return collected
        union_type = getattr(types, "UnionType", None)
        if union_type is not None and isinstance(value, union_type):
            collected = []
            for entry in value.__args__:
                flat = self._flatten_type_spec(entry)
                if flat is None:
                    return None
                collected.extend(flat)
            return collected
        return None
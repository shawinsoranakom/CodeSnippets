def __iadd__(self, other: "NodeExecutionStats") -> "NodeExecutionStats":
        """Mutate this instance by adding another NodeExecutionStats.

        Avoids calling model_dump() twice per merge (called on every
        merge_stats() from ~20+ blocks); reads via getattr/vars instead.
        """
        if not isinstance(other, NodeExecutionStats):
            return NotImplemented

        for key in type(other).model_fields:
            value = getattr(other, key)
            if value is None:
                # Never overwrite an existing value with None
                continue
            current = getattr(self, key, None)
            if current is None:
                # Field doesn't exist yet or is None, just set it
                setattr(self, key, value)
            elif isinstance(value, dict) and isinstance(current, dict):
                current.update(value)
            elif isinstance(value, (int, float)) and isinstance(current, (int, float)):
                setattr(self, key, current + value)
            elif isinstance(value, list) and isinstance(current, list):
                current.extend(value)
            else:
                setattr(self, key, value)

        return self
def items(self) -> Set[Tuple[str, Any]]:  # type: ignore[override]
        return {(k, self[k]) for k in self}
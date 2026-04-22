def values(self) -> Set[Any]:  # type: ignore[override]
        return {self[wid] for wid in self}
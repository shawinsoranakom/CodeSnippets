def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value
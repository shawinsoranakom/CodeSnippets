def flatten(self, value: Iterable[Any], levels: int | None = None) -> list[Any]:
        """Flatten list of lists."""
        if not isinstance(value, Iterable) or isinstance(value, str):
            raise TypeError(f"flatten expected a list, got {type(value).__name__}")

        flattened: list[Any] = []
        for item in value:
            if isinstance(item, Iterable) and not isinstance(item, str):
                if levels is None:
                    flattened.extend(self.flatten(item))
                elif levels >= 1:
                    flattened.extend(self.flatten(item, levels=(levels - 1)))
                else:
                    flattened.append(item)
            else:
                flattened.append(item)
        return flattened
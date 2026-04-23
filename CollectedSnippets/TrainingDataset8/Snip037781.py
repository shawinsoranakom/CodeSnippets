def maybe_allow_widgets(self, allow: bool) -> Iterator[None]:
        if allow:
            with self.allow_widgets():
                yield
        else:
            yield
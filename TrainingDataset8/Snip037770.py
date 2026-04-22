def allow_widgets(self) -> Iterator[None]:
        self._allow_widgets += 1
        try:
            yield
        finally:
            self._allow_widgets -= 1
            assert self._allow_widgets >= 0
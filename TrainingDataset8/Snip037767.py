def maybe_suppress_cached_st_function_warning(
        self, suppress: bool
    ) -> Iterator[None]:
        if suppress:
            with self.suppress_cached_st_function_warning():
                yield
        else:
            yield
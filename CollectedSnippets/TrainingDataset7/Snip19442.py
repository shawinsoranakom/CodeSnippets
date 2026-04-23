def _check_engines(self, engines):
        return list(
            chain.from_iterable(e._check_string_if_invalid_is_string() for e in engines)
        )
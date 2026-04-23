def _add_batch_dims(
        self, t: torch.Tensor | None, levels_: list[Any]
    ) -> torch.Tensor | None:
        levels = list(levels_)

        while True:
            min_real_index = -1
            min_index = -1
            min_value = float("inf")  # INT_MAX equivalent
            i = 0
            r = 0

            for r, l in enumerate(levels):
                if not l.is_none():
                    if not l.is_positional() and l.dim()._level < min_value:
                        min_value = l.dim()._level
                        min_index = i
                        min_real_index = r
                    i += 1

            if min_index == -1:
                return t

            if t is None:
                raise AssertionError("Expected t to be non-None")
            t = torch._C._functorch._add_batch_dim(t, min_index, int(min_value))

            levels[min_real_index] = DimEntry()
        return None
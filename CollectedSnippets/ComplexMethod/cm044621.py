def get_padding(first_row: bool, last_row: bool) -> Tuple[int, int, int, int]:
            cached = _padding_cache.get((first_row, last_row))
            if cached:
                return cached
            top, right, bottom, left = padding

            if collapse_padding:
                if not first_column:
                    left = max(0, left - right)
                if not last_row:
                    bottom = max(0, top - bottom)

            if not pad_edge:
                if first_column:
                    left = 0
                if last_column:
                    right = 0
                if first_row:
                    top = 0
                if last_row:
                    bottom = 0
            _padding = (top, right, bottom, left)
            _padding_cache[(first_row, last_row)] = _padding
            return _padding
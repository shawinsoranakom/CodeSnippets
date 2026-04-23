def _update(delta: int, size: int) -> None:
                assert 0 < size <= 8
                # first byte - use 13 (no column info) is positions is
                # malformed, otherwise use 14 (long form)
                other_varints: tuple[int, ...] = ()
                if (
                    positions
                    and positions.lineno is not None
                    and positions.end_lineno is not None
                    and positions.col_offset is not None
                    and positions.end_col_offset is not None
                ):
                    linetable.append(0b1_1110_000 + size - 1)
                    # for whatever reason, column offset needs `+ 1`
                    # https://github.com/python/cpython/blob/1931c2a438c50e6250725c84dff94fc760b9b951/Python/compile.c#L7603
                    other_varints = (
                        positions.end_lineno - positions.lineno,
                        positions.col_offset + 1,
                        positions.end_col_offset + 1,
                    )
                else:
                    linetable.append(0b1_1101_000 + size - 1)
                # encode signed int
                if delta < 0:
                    delta = ((-delta) << 1) | 1
                else:
                    delta <<= 1
                # encode unsigned int
                linetable.extend(encode_varint(delta))
                for n in other_varints:
                    linetable.extend(encode_varint(n))
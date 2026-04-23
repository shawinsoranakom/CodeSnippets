def as_index_list(v: object) -> List[int]:
            if _is_range_value(v):
                slider_value = [index_(opt, val) for val in v]
                start, end = slider_value
                if start > end:
                    slider_value = [end, start]
                return slider_value
            else:
                # Simplify future logic by always making value a list
                try:
                    return [index_(opt, v)]
                except ValueError:
                    if value is not None:
                        raise

                    return [0]
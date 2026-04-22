def _as_index_list(self, v: object) -> List[int]:
        if _is_range_value(v):
            slider_value = [index_(self.options, val) for val in v]
            start, end = slider_value
            if start > end:
                slider_value = [end, start]
            return slider_value
        else:
            return [index_(self.options, v)]
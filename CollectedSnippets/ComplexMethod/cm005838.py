def test_max_items_none(self, lst: list) -> None:
        result: list = serialize(lst, max_items=None)
        # NaN/Inf floats are sanitized to None, so compare element-wise
        assert len(result) == len(lst)
        for r, v in zip(result, lst, strict=False):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                assert r is None
            else:
                assert r == v
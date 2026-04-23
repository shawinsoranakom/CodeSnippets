def test_list_truncation(self, lst: list) -> None:
        result: list = serialize(lst, max_items=MAX_ITEMS_LENGTH)
        if len(lst) > MAX_ITEMS_LENGTH:
            assert len(result) == MAX_ITEMS_LENGTH + 1
            assert f"... [truncated {len(lst) - MAX_ITEMS_LENGTH} items]" in result
        else:
            # NaN/Inf floats are sanitized to None, so compare element-wise
            assert len(result) == len(lst)
            for r, v in zip(result, lst, strict=False):
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    assert r is None
                else:
                    assert r == v
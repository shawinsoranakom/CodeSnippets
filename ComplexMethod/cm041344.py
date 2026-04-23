def test_comparison_operation_mapping(self):
        a = 3
        b = 4

        assert not COMPARISON_OPS.get("GreaterThanOrEqualToThreshold")(a, b)
        assert COMPARISON_OPS.get("GreaterThanOrEqualToThreshold")(a, a)
        assert COMPARISON_OPS.get("GreaterThanOrEqualToThreshold")(b, a)

        assert not COMPARISON_OPS.get("GreaterThanThreshold")(a, b)
        assert not COMPARISON_OPS.get("GreaterThanThreshold")(a, a)
        assert COMPARISON_OPS.get("GreaterThanThreshold")(b, a)

        assert COMPARISON_OPS.get("LessThanThreshold")(a, b)
        assert not COMPARISON_OPS.get("LessThanThreshold")(a, a)
        assert not COMPARISON_OPS.get("LessThanThreshold")(b, a)

        assert COMPARISON_OPS.get("LessThanOrEqualToThreshold")(a, b)
        assert COMPARISON_OPS.get("LessThanOrEqualToThreshold")(a, a)
        assert not COMPARISON_OPS.get("LessThanOrEqualToThreshold")(b, a)
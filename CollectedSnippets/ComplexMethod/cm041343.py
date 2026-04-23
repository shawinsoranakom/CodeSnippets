def test_qualifier_is_alias(self):
        assert qualifier_is_alias("abczABCZ")
        assert qualifier_is_alias("a01239")
        assert qualifier_is_alias("1numeric")
        assert qualifier_is_alias("2024-01-01")
        assert not qualifier_is_alias("20240101")
        assert not qualifier_is_alias("invalid-with-$-char")
        assert not qualifier_is_alias("invalid-with-?-char")
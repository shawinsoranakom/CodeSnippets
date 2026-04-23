def test_is_qualifier_expression(self):
        assert is_qualifier_expression("abczABCZ")
        assert is_qualifier_expression("a01239")
        assert is_qualifier_expression("1numeric")
        assert is_qualifier_expression("-")
        assert is_qualifier_expression("_")
        assert is_qualifier_expression("valid-with-$-inside")
        assert not is_qualifier_expression("invalid-with-?-char")
        assert not is_qualifier_expression("")
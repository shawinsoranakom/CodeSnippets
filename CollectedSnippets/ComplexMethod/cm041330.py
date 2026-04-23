def test_str_to_bool(self):
        assert common.str_to_bool("true") is True
        assert common.str_to_bool("True") is True

        assert common.str_to_bool("1") is False
        assert common.str_to_bool("0") is False
        assert common.str_to_bool("TRUE") is False
        assert common.str_to_bool("false") is False
        assert common.str_to_bool("False") is False

        assert common.str_to_bool(0) == 0
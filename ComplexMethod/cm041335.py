def test_format_number(self):
        fn = common.format_number
        assert fn(12, decimals=0) == "12"
        assert fn(12, decimals=1) == "12"
        assert fn(12.421, decimals=0) == "12"
        assert fn(12.521, decimals=0) == "13"
        assert fn(12.521, decimals=2) == "12.52"
        assert fn(12.521, decimals=3) == "12.521"
        assert fn(12.521, decimals=4) == "12.521"
        assert fn(-12.521, decimals=4) == "-12.521"
        assert fn(-1.2234354123e3, decimals=4) == "-1223.4354"
def test_format_bytes(self):
        fn = common.format_bytes

        assert fn(1) == "1B"
        assert fn(100) == "100B"
        assert fn(999) == "999B"
        assert fn(1e3) == "1KB"
        assert fn(1e6) == "1MB"
        assert fn(1e7) == "10MB"
        assert fn(1e8) == "100MB"
        assert fn(1e9) == "1GB"
        assert fn(1e12) == "1TB"

        # comma values
        assert fn(1e12 + 1e11) == "1.1TB"
        assert fn(1e15) == "1000TB"

        # string input
        assert fn("123") == "123B"
        # invalid number
        assert fn("abc") == "n/a"
        # negative number
        assert fn(-1) == "n/a"
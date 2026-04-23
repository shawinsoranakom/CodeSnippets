def test_extract_jsonpath(self):
        obj = {"a": {"b": [{"c": 123}, "foo"]}, "e": 234}
        result = common.extract_jsonpath(obj, "$.a.b")
        assert result == [{"c": 123}, "foo"]
        result = common.extract_jsonpath(obj, "$.a.b.c")
        assert not result
        result = common.extract_jsonpath(obj, "$.foobar")
        assert not result
        result = common.extract_jsonpath(obj, "$.e")
        assert result == 234
        result = common.extract_jsonpath(obj, "$.a.b[0]")
        assert result == {"c": 123}
        result = common.extract_jsonpath(obj, "$.a.b[0].c")
        assert result == 123
        result = common.extract_jsonpath(obj, "$.a.b[1]")
        assert result == "foo"
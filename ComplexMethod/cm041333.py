def test_obj_to_xml(self):
        fn = common.obj_to_xml
        # primitive
        assert fn(42) == "42"
        assert fn(False) == "False"
        assert fn("a") == "a"
        # dict only
        assert fn({"foo": "bar"}) == "<foo>bar</foo>"
        assert fn({"a": 42}) == "<a>42</a>"
        assert fn({"a": 42, "foo": "bar"}) == "<a>42</a><foo>bar</foo>"
        # list of dicts
        assert fn([{"a": 42}, {"a": 43}]) == "<a>42</a><a>43</a>"
        # dict with lists
        assert fn({"f": [{"a": 42}, {"a": 43}]}) == "<f><a>42</a><a>43</a></f>"
        # empty types
        assert fn(None) == "None"
        assert fn("") == ""
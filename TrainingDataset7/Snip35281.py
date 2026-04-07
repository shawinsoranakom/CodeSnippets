def test_simple_not_equal_raise(self):
        json1 = '{"attr1": "foo", "attr2":"baz"}'
        json2 = '{"attr1": "foo", "attr2":"baz"}'
        with self.assertRaises(AssertionError):
            self.assertJSONNotEqual(json1, json2)
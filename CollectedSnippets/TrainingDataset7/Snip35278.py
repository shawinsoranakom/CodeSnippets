def test_simple_equal_raise(self):
        json1 = '{"attr1": "foo", "attr2":"baz"}'
        json2 = '{"attr2":"baz"}'
        with self.assertRaises(AssertionError):
            self.assertJSONEqual(json1, json2)
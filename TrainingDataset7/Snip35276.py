def test_simple_equal(self):
        json1 = '{"attr1": "foo", "attr2":"baz"}'
        json2 = '{"attr1": "foo", "attr2":"baz"}'
        self.assertJSONEqual(json1, json2)
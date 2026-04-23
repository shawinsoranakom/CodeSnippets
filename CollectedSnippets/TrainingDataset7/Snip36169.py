def test_repr(self):
        d = MultiValueDict({"key": "value"})
        self.assertEqual(repr(d), "<MultiValueDict: {'key': 'value'}>")
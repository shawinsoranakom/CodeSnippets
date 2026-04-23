def test_dict_items(self):
        a = types.MappingProxyType({"a": 1}).items()
        b = types.MappingProxyType({"a": 1}).items()
        c = types.MappingProxyType({"c": 1}).items()

        assert is_type(a, "builtins.dict_items")
        self.assertEqual(get_hash(a), get_hash(b))
        self.assertNotEqual(get_hash(a), get_hash(c))
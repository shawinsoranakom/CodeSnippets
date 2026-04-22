def test_mappingproxy(self):
        a = types.MappingProxyType({"a": 1})
        b = types.MappingProxyType({"a": 1})
        c = types.MappingProxyType({"c": 1})

        self.assertEqual(get_hash(a), get_hash(b))
        self.assertNotEqual(get_hash(a), get_hash(c))
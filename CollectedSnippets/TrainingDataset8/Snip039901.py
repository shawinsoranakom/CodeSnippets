def test_attr_dict_is_mapping_but_not_built_in_dict(self, *mocks):
        """Verify that AttrDict implements Mapping, but not built-in Dict"""
        self.assertIsInstance(self.secrets.subsection, Mapping)
        self.assertIsInstance(self.secrets.subsection, MappingABC)
        self.assertNotIsInstance(self.secrets.subsection, MutableMapping)
        self.assertNotIsInstance(self.secrets.subsection, MutableMappingABC)
        self.assertNotIsInstance(self.secrets.subsection, dict)
def test_fields_cache_descriptor(self):
        self.assertIsInstance(ModelState.fields_cache, ModelStateFieldsCacheDescriptor)
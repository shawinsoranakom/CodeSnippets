def test_serialize_decorated_functions(self):
        self.assertSerializedEqual(function_with_decorator)
        self.assertSerializedEqual(function_with_cache)
        self.assertSerializedEqual(function_with_lru_cache)
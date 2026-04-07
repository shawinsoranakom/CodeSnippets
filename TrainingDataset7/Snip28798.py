def test_clear_cache_clears_relation_tree(self):
        # The apps.clear_cache is setUp() should have deleted all trees.
        # Exclude abstract models that are not included in the Apps registry
        # and have no cache.
        all_models_with_cache = (m for m in self.all_models if not m._meta.abstract)
        for m in all_models_with_cache:
            self.assertNotIn("_relation_tree", m._meta.__dict__)
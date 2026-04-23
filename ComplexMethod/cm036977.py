def test_add_pickle_unpickle(self):
        cache = StandaloneCompiledArtifacts()

        artifacts = {
            ("mod1", "shape1"): b"m1s1_artifact",
            ("mod1", "shape2"): b"m1s2_artifact",
            ("mod2", "shape1"): b"m2s1_artifact",
            ("mod2", "shape2"): b"m2s2_artifact",
        }

        for (submod, shape), data in artifacts.items():
            cache.insert(submod, shape, data)

        assert cache.num_entries() == 4
        assert cache.num_artifacts() == 4

        for (submod, shape), expected_data in artifacts.items():
            retrieved_data = cache.get(submod, shape)
            assert retrieved_data == expected_data

        pickled = pickle.dumps(cache)
        restored_cache = pickle.loads(pickled)

        for (submod, shape), expected_data in artifacts.items():
            retrieved_data = restored_cache.get(submod, shape)
            assert retrieved_data == expected_data
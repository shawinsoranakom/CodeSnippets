def test_invalid_key(self, key):
        with pytest.raises(AssertionError) as e:
            ConfigOption(key)
        self.assertEqual('Key "%s" has invalid format.' % key, str(e.value))
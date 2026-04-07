def test_missing_deferred_key_raises_keyerror(self):
        parent = {"settings": {"theme": "dark"}}
        sub = DeferredSubDict(parent, "nonexistent")
        with self.assertRaises(KeyError):
            sub["anything"]
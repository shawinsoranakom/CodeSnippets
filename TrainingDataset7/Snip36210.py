def test_missing_child_key_raises_keyerror(self):
        parent = {"settings": {"theme": "dark"}}
        sub = DeferredSubDict(parent, "settings")
        with self.assertRaises(KeyError):
            sub["nonexistent"]
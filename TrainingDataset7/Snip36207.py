def test_basic(self):
        parent = {
            "settings": {"theme": "dark", "language": "en"},
            "config": {"enabled": True, "timeout": 30},
        }
        sub = DeferredSubDict(parent, "settings")
        self.assertEqual(sub["theme"], "dark")
        self.assertEqual(sub["language"], "en")
        with self.assertRaises(KeyError):
            sub["enabled"]
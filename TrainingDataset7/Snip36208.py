def test_reflects_changes_in_parent(self):
        parent = {"settings": {"theme": "dark"}}
        sub = DeferredSubDict(parent, "settings")
        parent["settings"]["theme"] = "light"
        self.assertEqual(sub["theme"], "light")
        parent["settings"]["mode"] = "tight"
        self.assertEqual(sub["mode"], "tight")
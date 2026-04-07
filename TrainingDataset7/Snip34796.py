def test_contextlist_get(self):
        c1 = Context({"hello": "world", "goodbye": "john"})
        c2 = Context({"goodbye": "world", "python": "rocks"})
        k = ContextList([c1, c2])
        self.assertEqual(k.get("hello"), "world")
        self.assertEqual(k.get("goodbye"), "john")
        self.assertEqual(k.get("python"), "rocks")
        self.assertEqual(k.get("nonexistent", "default"), "default")
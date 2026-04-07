def test_multiple_keys(self):
        """Test QueryDict with two key/value pairs with same keys."""

        q = QueryDict("vote=yes&vote=no")

        self.assertEqual(q["vote"], "no")
        with self.assertRaises(AttributeError):
            q.__setitem__("something", "bar")

        self.assertEqual(q.get("vote", "default"), "no")
        self.assertEqual(q.get("foo", "default"), "default")
        self.assertEqual(q.getlist("vote"), ["yes", "no"])
        self.assertEqual(q.getlist("foo"), [])

        with self.assertRaises(AttributeError):
            q.setlist("foo", ["bar", "baz"])
        with self.assertRaises(AttributeError):
            q.setlist("foo", ["bar", "baz"])
        with self.assertRaises(AttributeError):
            q.appendlist("foo", ["bar"])

        self.assertIn("vote", q)
        self.assertNotIn("foo", q)
        self.assertEqual(list(q), ["vote"])
        self.assertEqual(list(q.items()), [("vote", "no")])
        self.assertEqual(list(q.lists()), [("vote", ["yes", "no"])])
        self.assertEqual(list(q.keys()), ["vote"])
        self.assertEqual(list(q.values()), ["no"])
        self.assertEqual(len(q), 1)

        with self.assertRaises(AttributeError):
            q.update({"foo": "bar"})
        with self.assertRaises(AttributeError):
            q.pop("foo")
        with self.assertRaises(AttributeError):
            q.popitem()
        with self.assertRaises(AttributeError):
            q.clear()
        with self.assertRaises(AttributeError):
            q.setdefault("foo", "bar")
        with self.assertRaises(AttributeError):
            q.__delitem__("vote")
def test_single_key_value(self):
        """Test QueryDict with one key/value pair"""

        q = QueryDict("foo=bar")
        self.assertEqual(q["foo"], "bar")
        with self.assertRaises(KeyError):
            q.__getitem__("bar")
        with self.assertRaises(AttributeError):
            q.__setitem__("something", "bar")

        self.assertEqual(q.get("foo", "default"), "bar")
        self.assertEqual(q.get("bar", "default"), "default")
        self.assertEqual(q.getlist("foo"), ["bar"])
        self.assertEqual(q.getlist("bar"), [])

        with self.assertRaises(AttributeError):
            q.setlist("foo", ["bar"])
        with self.assertRaises(AttributeError):
            q.appendlist("foo", ["bar"])

        self.assertIn("foo", q)
        self.assertNotIn("bar", q)

        self.assertEqual(list(q), ["foo"])
        self.assertEqual(list(q.items()), [("foo", "bar")])
        self.assertEqual(list(q.lists()), [("foo", ["bar"])])
        self.assertEqual(list(q.keys()), ["foo"])
        self.assertEqual(list(q.values()), ["bar"])
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

        self.assertEqual(q.urlencode(), "foo=bar")
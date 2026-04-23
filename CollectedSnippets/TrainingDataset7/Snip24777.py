def test_immutability(self):
        q = QueryDict()
        with self.assertRaises(AttributeError):
            q.__setitem__("something", "bar")
        with self.assertRaises(AttributeError):
            q.setlist("foo", ["bar"])
        with self.assertRaises(AttributeError):
            q.appendlist("foo", ["bar"])
        with self.assertRaises(AttributeError):
            q.update({"foo": "bar"})
        with self.assertRaises(AttributeError):
            q.pop("foo")
        with self.assertRaises(AttributeError):
            q.popitem()
        with self.assertRaises(AttributeError):
            q.clear()
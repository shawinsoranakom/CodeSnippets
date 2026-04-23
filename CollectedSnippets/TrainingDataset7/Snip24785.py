def test_basic_mutable_operations(self):
        q = QueryDict(mutable=True)
        q["name"] = "john"
        self.assertEqual(q.get("foo", "default"), "default")
        self.assertEqual(q.get("name", "default"), "john")
        self.assertEqual(q.getlist("name"), ["john"])
        self.assertEqual(q.getlist("foo"), [])

        q.setlist("foo", ["bar", "baz"])
        self.assertEqual(q.get("foo", "default"), "baz")
        self.assertEqual(q.getlist("foo"), ["bar", "baz"])

        q.appendlist("foo", "another")
        self.assertEqual(q.getlist("foo"), ["bar", "baz", "another"])
        self.assertEqual(q["foo"], "another")
        self.assertIn("foo", q)

        self.assertCountEqual(q, ["foo", "name"])
        self.assertCountEqual(q.items(), [("foo", "another"), ("name", "john")])
        self.assertCountEqual(
            q.lists(), [("foo", ["bar", "baz", "another"]), ("name", ["john"])]
        )
        self.assertCountEqual(q.keys(), ["foo", "name"])
        self.assertCountEqual(q.values(), ["another", "john"])

        q.update({"foo": "hello"})
        self.assertEqual(q["foo"], "hello")
        self.assertEqual(q.get("foo", "not available"), "hello")
        self.assertEqual(q.getlist("foo"), ["bar", "baz", "another", "hello"])
        self.assertEqual(q.pop("foo"), ["bar", "baz", "another", "hello"])
        self.assertEqual(q.pop("foo", "not there"), "not there")
        self.assertEqual(q.get("foo", "not there"), "not there")
        self.assertEqual(q.setdefault("foo", "bar"), "bar")
        self.assertEqual(q["foo"], "bar")
        self.assertEqual(q.getlist("foo"), ["bar"])
        self.assertIn(q.urlencode(), ["foo=bar&name=john", "name=john&foo=bar"])

        q.clear()
        self.assertEqual(len(q), 0)
def test_defer_subclass(self):
        # You can defer a field on a subclass
        obj = BigChild.objects.defer("other").get(name="b1")
        self.assert_delayed(obj, 1)
        self.assertEqual(obj.name, "b1")
        self.assertEqual(obj.value, "foo")
        self.assertEqual(obj.other, "bar")
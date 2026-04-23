def test_defer_baseclass_when_subclass_has_added_field(self):
        # You can defer a field on a baseclass
        obj = BigChild.objects.defer("value").get(name="b1")
        self.assert_delayed(obj, 1)
        self.assertEqual(obj.name, "b1")
        self.assertEqual(obj.value, "foo")
        self.assertEqual(obj.other, "bar")
def test_only_baseclass_when_subclass_has_added_field(self):
        # You can retrieve a single field on a baseclass
        obj = BigChild.objects.only("name").get(name="b1")
        # when inherited model, its PK is also fetched, hence '4' deferred
        # fields.
        self.assert_delayed(obj, 4)
        self.assertEqual(obj.name, "b1")
        self.assertEqual(obj.value, "foo")
        self.assertEqual(obj.other, "bar")
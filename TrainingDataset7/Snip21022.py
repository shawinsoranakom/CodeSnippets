def test_only_baseclass_when_subclass_has_no_added_fields(self):
        # You can retrieve a single column on a base class with no fields
        Child.objects.create(name="c1", value="foo", related=self.s1)
        obj = Child.objects.only("name").get(name="c1")
        # on an inherited model, its PK is also fetched, hence '3' deferred
        # fields.
        self.assert_delayed(obj, 3)
        self.assertEqual(obj.name, "c1")
        self.assertEqual(obj.value, "foo")
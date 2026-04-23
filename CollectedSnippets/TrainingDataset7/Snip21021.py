def test_defer_baseclass_when_subclass_has_no_added_fields(self):
        # Regression for #10572 - A subclass with no extra fields can defer
        # fields from the base class
        Child.objects.create(name="c1", value="foo", related=self.s1)
        # You can defer a field on a baseclass when the subclass has no fields
        obj = Child.objects.defer("value").get(name="c1")
        self.assert_delayed(obj, 1)
        self.assertEqual(obj.name, "c1")
        self.assertEqual(obj.value, "foo")
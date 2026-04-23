def test_for_update_after_from(self):
        features_class = connections["default"].features.__class__
        attribute_to_patch = "%s.%s.for_update_after_from" % (
            features_class.__module__,
            features_class.__name__,
        )
        with mock.patch(attribute_to_patch, return_value=True):
            with transaction.atomic():
                self.assertIn(
                    "FOR UPDATE WHERE",
                    str(Person.objects.filter(name="foo").select_for_update().query),
                )
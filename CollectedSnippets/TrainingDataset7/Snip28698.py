def test_shadow_parent_attribute_with_field(self):
        class ScalarParent(models.Model):
            foo = 1

        class ScalarOverride(ScalarParent):
            foo = models.IntegerField()

        self.assertEqual(type(ScalarOverride.foo), DeferredAttribute)
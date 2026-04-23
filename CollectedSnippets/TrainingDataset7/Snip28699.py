def test_shadow_parent_property_with_field(self):
        class PropertyParent(models.Model):
            @property
            def foo(self):
                pass

        class PropertyOverride(PropertyParent):
            foo = models.IntegerField()

        self.assertEqual(type(PropertyOverride.foo), DeferredAttribute)
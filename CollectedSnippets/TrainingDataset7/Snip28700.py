def test_shadow_parent_method_with_field(self):
        class MethodParent(models.Model):
            def foo(self):
                pass

        class MethodOverride(MethodParent):
            foo = models.IntegerField()

        self.assertEqual(type(MethodOverride.foo), DeferredAttribute)
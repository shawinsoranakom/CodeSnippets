def test_nested(self, method_apps):
        class MethodDecoration(models.Model):
            pass

        with isolate_apps("test_utils") as context_apps:

            class ContextManager(models.Model):
                pass

            with isolate_apps("test_utils") as nested_context_apps:

                class NestedContextManager(models.Model):
                    pass

        self.assertEqual(MethodDecoration._meta.apps, method_apps)
        self.assertEqual(ContextManager._meta.apps, context_apps)
        self.assertEqual(NestedContextManager._meta.apps, nested_context_apps)
def test_context_manager(self):
        with isolate_apps("test_utils") as context_apps:

            class ContextManager(models.Model):
                pass

        self.assertEqual(ContextManager._meta.apps, context_apps)
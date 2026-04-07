def test_method_decoration(self, method_apps):
        class MethodDecoration(models.Model):
            pass

        self.assertEqual(MethodDecoration._meta.apps, method_apps)
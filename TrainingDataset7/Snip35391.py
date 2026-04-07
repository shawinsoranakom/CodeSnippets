def test_class_decoration(self):
        class ClassDecoration(models.Model):
            pass

        self.assertEqual(ClassDecoration._meta.apps, self.class_apps)
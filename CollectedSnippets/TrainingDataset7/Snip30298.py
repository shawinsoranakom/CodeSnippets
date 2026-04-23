def test_no_base_classes(self):
        msg = "Proxy model 'NoBaseClasses' has no non-abstract model base class."
        with self.assertRaisesMessage(TypeError, msg):

            class NoBaseClasses(models.Model):
                class Meta:
                    proxy = True
def test_upload_to_callable_not_checked(self):
        def callable(instance, filename):
            return "/" + filename

        class Model(models.Model):
            field = models.FileField(upload_to=callable)

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(), [])
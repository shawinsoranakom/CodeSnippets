def test_image_field(self):
        field = models.ImageField(
            upload_to="foo/barness", width_field="width", height_field="height"
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ImageField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs,
            {
                "upload_to": "foo/barness",
                "width_field": "width",
                "height_field": "height",
            },
        )
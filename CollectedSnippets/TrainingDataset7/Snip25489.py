def test_pillow_installed(self):
        try:
            from PIL import Image  # NOQA
        except ImportError:
            pillow_installed = False
        else:
            pillow_installed = True

        class Model(models.Model):
            field = models.ImageField(upload_to="somewhere")

        field = Model._meta.get_field("field")
        errors = field.check()
        expected = (
            []
            if pillow_installed
            else [
                Error(
                    "Cannot use ImageField because Pillow is not installed.",
                    hint=(
                        "Get Pillow at https://pypi.org/project/Pillow/ "
                        'or run command "python -m pip install Pillow".'
                    ),
                    obj=field,
                    id="fields.E210",
                ),
            ]
        )
        self.assertEqual(errors, expected)
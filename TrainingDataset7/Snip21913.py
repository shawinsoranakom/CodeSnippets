def test_callable_base_class_error_raises(self):
        class NotStorage:
            pass

        msg = (
            "FileField.storage must be a subclass/instance of "
            "django.core.files.storage.base.Storage"
        )
        for invalid_type in (NotStorage, str, list, set, tuple):
            with self.subTest(invalid_type=invalid_type):
                with self.assertRaisesMessage(TypeError, msg):
                    FileField(storage=invalid_type)
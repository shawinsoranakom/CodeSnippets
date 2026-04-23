def decorate_class(self, cls):
        from django.test import SimpleTestCase

        if not issubclass(cls, SimpleTestCase):
            raise ValueError(
                "Only subclasses of Django SimpleTestCase can be decorated "
                "with override_settings"
            )
        self.save_options(cls)
        return cls
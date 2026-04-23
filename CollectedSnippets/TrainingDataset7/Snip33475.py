def setUpClass(cls):
        cls.engine = Engine(libraries={"cache": "django.templatetags.cache"})
        super().setUpClass()
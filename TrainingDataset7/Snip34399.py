def setUpClass(cls):
        cls.engine = Engine(
            loaders=[
                (
                    "django.template.loaders.locmem.Loader",
                    {
                        "index.html": "index",
                    },
                )
            ],
        )
        super().setUpClass()
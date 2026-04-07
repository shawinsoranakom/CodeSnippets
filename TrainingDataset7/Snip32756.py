def test_dirs_pathlib(self):
        engine = DjangoTemplates(
            {
                "DIRS": [Path(__file__).parent / "templates" / "template_backends"],
                "APP_DIRS": False,
                "NAME": "django",
                "OPTIONS": {},
            }
        )
        template = engine.get_template("hello.html")
        self.assertEqual(template.render({"name": "Joe"}), "Hello Joe!\n")
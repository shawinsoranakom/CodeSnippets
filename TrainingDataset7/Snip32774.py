def test_dirs_pathlib(self):
        engine = Jinja2(
            {
                "DIRS": [Path(__file__).parent / "templates" / "template_backends"],
                "APP_DIRS": False,
                "NAME": "jinja2",
                "OPTIONS": {},
            }
        )
        template = engine.get_template("hello.html")
        self.assertEqual(template.render({"name": "Joe"}), "Hello Joe!")
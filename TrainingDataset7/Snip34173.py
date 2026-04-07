def test_get_template_directories(self):
        self.assertSetEqual(
            autoreload.get_template_directories(),
            {
                ROOT / "templates",
            },
        )
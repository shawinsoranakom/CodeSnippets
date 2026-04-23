def test_sections_order(self):
        sections = sorted(
            [
                "_test",
                "browser",
                "client",
                "theme",
                "deprecation",
                "global",
                "logger",
                "mapbox",
                "runner",
                "server",
                "ui",
            ]
        )
        keys = sorted(list(config._section_descriptions.keys()))
        self.assertEqual(sections, keys)
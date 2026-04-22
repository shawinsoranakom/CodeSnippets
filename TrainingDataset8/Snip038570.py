def setUp(self):
        self.patches = [
            patch.object(
                config, "_section_descriptions", new=copy.deepcopy(SECTION_DESCRIPTIONS)
            ),
            patch.object(config, "_config_options", new=copy.deepcopy(CONFIG_OPTIONS)),
        ]

        for p in self.patches:
            p.start()
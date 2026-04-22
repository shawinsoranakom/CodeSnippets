def setUp(self):
        # Credentials._singleton should be None here, but a mis-behaving
        # test may have left it intact.
        Credentials._singleton = None

        cli.name = "streamlit"
        self.runner = CliRunner()

        self.patches = [
            patch.object(config._on_config_parsed, "send"),
            # Make sure the calls to `streamlit run` in this file don't unset
            # the config options loaded in conftest.py.
            patch.object(streamlit.web.bootstrap, "load_config_options"),
        ]

        for p in self.patches:
            p.start()
def test_set_option(self):
        with self.assertLogs(logger="streamlit.config", level="WARNING") as cm:
            config._set_option("not.defined", "no.value", "test")
        # cm.output is a list of messages and there shouldn't be any other messages besides one created by this test
        self.assertIn(
            '"not.defined" is not a valid config option. If you previously had this config option set, it may have been removed.',
            cm.output[0],
        )

        config._set_option("client.caching", "test", "test")
        self.assertEqual("test", config.get_option("client.caching"))
def test_server_headless_via_atom_plugin(self):
        os.environ["IS_RUNNING_IN_STREAMLIT_EDITOR_PLUGIN"] = "True"

        self.assertEqual(True, config.get_option("server.headless"))

        del os.environ["IS_RUNNING_IN_STREAMLIT_EDITOR_PLUGIN"]
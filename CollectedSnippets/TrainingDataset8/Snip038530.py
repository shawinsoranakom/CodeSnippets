def test_no_path_and_no_url(self):
        """Fail if neither path nor url is provided."""
        with pytest.raises(StreamlitAPIException) as exception_message:
            components.declare_component("test", path=None, url=None)
        self.assertEqual(
            "Either 'path' or 'url' must be set, but not both.",
            str(exception_message.value),
        )
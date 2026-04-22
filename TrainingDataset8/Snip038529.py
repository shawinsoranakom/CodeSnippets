def test_path_and_url(self):
        """Fail if path AND url are provided."""
        with pytest.raises(StreamlitAPIException) as exception_message:
            components.declare_component("test", path=PATH, url=URL)
        self.assertEqual(
            "Either 'path' or 'url' must be set, but not both.",
            str(exception_message.value),
        )
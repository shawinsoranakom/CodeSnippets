def test_streamlit_version(self):
        assert (
            STREAMLIT_RELEASE_VERSION != None and STREAMLIT_RELEASE_VERSION != ""
        ), "You must set the $STREAMLIT_RELEASE_VERSION env variable"
        assert STREAMLIT_RELEASE_VERSION in self.run_command(
            "streamlit version"
        ), f"Package version does not match the desired version of {STREAMLIT_RELEASE_VERSION}"
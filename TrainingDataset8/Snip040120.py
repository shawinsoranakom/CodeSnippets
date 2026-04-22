def test_generate_download_filename_from_title(self):
        """Test streamlit.string_util.generate_download_filename_from_title."""

        self.assertTrue(
            string_util.generate_download_filename_from_title(
                "app · Streamlit"
            ).startswith("App")
        )

        self.assertTrue(
            string_util.generate_download_filename_from_title(
                "app · Streamlit"
            ).startswith("App")
        )

        self.assertTrue(
            string_util.generate_download_filename_from_title(
                "App title here"
            ).startswith("AppTitleHere")
        )

        self.assertTrue(
            string_util.generate_download_filename_from_title(
                "Аптека, улица, фонарь"
            ).startswith("АптекаУлицаФонарь")
        )
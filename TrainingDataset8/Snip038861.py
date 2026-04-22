def test_image_to_url_adds_filenames_to_media_file_mgr(
        self, input_string: str, expected_mimetype: str, is_url: bool
    ):
        """if `image_to_url` is unable to open an image passed by name, it
        still passes the filename to MediaFileManager. (MediaFileManager may have a
        storage backend that's able to open the file, so it's up to the manager -
        and not image_to_url - to throw an error.)
        """
        # Mock out save_image_data to avoid polluting the cache for later tests
        with mock.patch(
            "streamlit.runtime.media_file_manager.MediaFileManager.add"
        ) as mock_mfm_add, mock.patch("streamlit.runtime.caching.save_media_data"):
            mock_mfm_add.return_value = "https://mockoutputurl.com"

            result = image.image_to_url(
                input_string,
                width=-1,
                clamp=False,
                channels="RGB",
                output_format="auto",
                image_id="mock_image_id",
            )

            if is_url:
                # URLs should be returned as-is, and should not result in a call to
                # MediaFileManager.add
                self.assertEqual(input_string, result)
                mock_mfm_add.assert_not_called()
            else:
                # Other strings should be passed to MediaFileManager.add
                self.assertEqual("https://mockoutputurl.com", result)
                mock_mfm_add.assert_called_once_with(
                    input_string, expected_mimetype, "mock_image_id"
                )
def test_add_bytes_and_filenames_to_mediafilemanager(
        self,
        media_data: MediaData,
        mimetype: str,
        media_kind: TestMediaKind,
        is_url: bool,
    ):
        """st.audio + st.video should register bytes and filenames with the
        MediaFileManager. URL-based media does not go through the MediaFileManager.
        """
        with mock.patch(
            "streamlit.runtime.media_file_manager.MediaFileManager.add"
        ) as mock_mfm_add, mock.patch("streamlit.runtime.caching.save_media_data"):
            mock_mfm_add.return_value = "https://mockoutputurl.com"

            if media_kind is TestMediaKind.AUDIO:
                st.audio(media_data, mimetype)
                element = self.get_delta_from_queue().new_element
                element_url = element.audio.url
            else:
                st.video(media_data, mimetype)
                element = self.get_delta_from_queue().new_element
                element_url = element.video.url

            if is_url:
                # URLs should be returned as-is, and should not result in a call to
                # MediaFileManager.add
                self.assertEqual(media_data, element_url)
                mock_mfm_add.assert_not_called()
            else:
                # Other strings, and audio data, should be passed to
                # MediaFileManager.add
                mock_mfm_add.assert_called_once_with(
                    media_data,
                    mimetype,
                    str(make_delta_path(RootContainer.MAIN, (), 0)),
                )
                self.assertEqual("https://mockoutputurl.com", element_url)
def test_marshall_images(self, data_in: image.AtomicImage, format: str):
        """Test streamlit.image.marshall_images.
        Need to test the following:
        * if list
        * if not list (is rgb vs is bgr)
        * if captions is not list but image is
        * if captions length doesn't match image length
        * if the caption is set.
        * PIL Images
        * Numpy Arrays
        * Url
        * Path
        * Bytes
        """
        mimetype = f"image/{format}"
        if isinstance(data_in, bytes):
            file_id = _calculate_file_id(data_in, mimetype=mimetype)
        else:
            file_id = _calculate_file_id(
                _np_array_to_bytes(data_in, output_format=format),
                mimetype=mimetype,
            )

        st.image(data_in, output_format=format)
        imglist = self.get_delta_from_queue().new_element.imgs
        self.assertEqual(len(imglist.imgs), 1)
        self.assertTrue(imglist.imgs[0].url.startswith(MEDIA_ENDPOINT))
        self.assertTrue(
            imglist.imgs[0].url.endswith(get_extension_for_mimetype(mimetype))
        )
        self.assertTrue(file_id in imglist.imgs[0].url)
def test_content_length_nonzero_starting_position_buffer(self):
        test_tuples = (
            ("BytesIO", io.BytesIO),
            ("UnseekableBytesIO", UnseekableBytesIO),
        )
        for buffer_class_name, BufferClass in test_tuples:
            with self.subTest(buffer_class_name=buffer_class_name):
                buffer = BufferClass(b"binary content")
                buffer.seek(10)
                response = FileResponse(buffer)
                self.assertEqual(response.headers["Content-Length"], "4")
def test_frame_empty_group_by_cols(self):
        frame = WindowFrame()
        self.assertEqual(frame.get_group_by_cols(), [])
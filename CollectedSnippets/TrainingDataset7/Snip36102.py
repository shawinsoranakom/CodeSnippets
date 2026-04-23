def test_nested_callable(self):
        def get_audio_choices():
            return [("vinyl", _("Vinyl")), ("cd", _("CD"))]

        def get_video_choices():
            return [("vhs", _("VHS Tape")), ("dvd", _("DVD"))]

        def get_media_choices():
            return [
                ("Audio", get_audio_choices),
                ("Video", get_video_choices),
                ("unknown", _("Unknown")),
            ]

        get_media_choices_spy = mock.Mock(wraps=get_media_choices)
        output = normalize_choices(get_media_choices_spy)

        get_media_choices_spy.assert_not_called()
        self.assertIsInstance(output, CallableChoiceIterator)
        self.assertEqual(output, self.expected_nested)
        get_media_choices_spy.assert_called_once()
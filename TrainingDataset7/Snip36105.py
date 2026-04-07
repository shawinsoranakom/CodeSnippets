def test_nested_iterator(self):
        def generate_audio_choices():
            yield "vinyl", _("Vinyl")
            yield "cd", _("CD")

        def generate_video_choices():
            yield "vhs", _("VHS Tape")
            yield "dvd", _("DVD")

        def generate_media_choices():
            yield "Audio", generate_audio_choices()
            yield "Video", generate_video_choices()
            yield "unknown", _("Unknown")

        choices = generate_media_choices()
        self.assertEqual(normalize_choices(choices), self.expected_nested)
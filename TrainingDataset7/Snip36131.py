def get_media_choices():
            return [
                ["Audio", get_audio_choices],
                ["Video", get_video_choices],
                ["unknown", _("Unknown")],
            ]
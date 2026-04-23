def generate_media_choices():
            yield "Audio", generate_audio_choices()
            yield "Video", generate_video_choices()
            yield "unknown", _("Unknown")
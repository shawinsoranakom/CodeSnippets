def _add_narration_to_video(
        self,
        video_abspath: str,
        audio_abspath: str,
        output_abspath: str,
        mix_mode: str,
        narration_volume: float,
        original_volume: float,
    ) -> None:
        """Add narration audio to video. Extracted for testability."""
        video = None
        final = None
        narration_original = None
        narration_scaled = None
        original = None

        try:
            strip_chapters_inplace(video_abspath)
            video = VideoFileClip(video_abspath)
            narration_original = AudioFileClip(audio_abspath)
            narration_scaled = narration_original.with_volume_scaled(narration_volume)
            narration = narration_scaled

            if mix_mode == "replace":
                final_audio = narration
            elif mix_mode == "mix":
                if video.audio:
                    original = video.audio.with_volume_scaled(original_volume)
                    final_audio = CompositeAudioClip([original, narration])
                else:
                    final_audio = narration
            else:  # ducking - apply stronger attenuation
                if video.audio:
                    # Ducking uses a much lower volume for original audio
                    ducking_volume = original_volume * 0.3
                    original = video.audio.with_volume_scaled(ducking_volume)
                    final_audio = CompositeAudioClip([original, narration])
                else:
                    final_audio = narration

            final = video.with_audio(final_audio)
            video_codec, audio_codec = get_video_codecs(output_abspath)
            final.write_videofile(
                output_abspath, codec=video_codec, audio_codec=audio_codec
            )

        finally:
            if original:
                original.close()
            if narration_scaled:
                narration_scaled.close()
            if narration_original:
                narration_original.close()
            if final:
                final.close()
            if video:
                video.close()
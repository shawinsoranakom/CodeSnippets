def _concat_videos(
        self,
        video_abspaths: list[str],
        output_abspath: str,
        transition: str,
        transition_duration: int,
    ) -> float:
        """Concatenate videos. Extracted for testability.

        Returns:
            Total duration of the concatenated video.
        """
        clips = []
        faded_clips = []
        final = None
        try:
            # Load clips
            for v in video_abspaths:
                strip_chapters_inplace(v)
                clips.append(VideoFileClip(v))

            # Validate transition_duration against shortest clip
            if transition in {"crossfade", "fade_black"} and transition_duration > 0:
                min_duration = min(c.duration for c in clips)
                if transition_duration >= min_duration:
                    raise BlockExecutionError(
                        message=(
                            f"transition_duration ({transition_duration}s) must be "
                            f"shorter than the shortest clip ({min_duration:.2f}s)"
                        ),
                        block_name=self.name,
                        block_id=str(self.id),
                    )

            if transition == "crossfade":
                for i, clip in enumerate(clips):
                    effects = []
                    if i > 0:
                        effects.append(CrossFadeIn(transition_duration))
                    if i < len(clips) - 1:
                        effects.append(CrossFadeOut(transition_duration))
                    if effects:
                        clip = clip.with_effects(effects)
                    faded_clips.append(clip)
                final = concatenate_videoclips(
                    faded_clips,
                    method="compose",
                    padding=-transition_duration,
                )
            elif transition == "fade_black":
                for clip in clips:
                    faded = clip.with_effects(
                        [FadeIn(transition_duration), FadeOut(transition_duration)]
                    )
                    faded_clips.append(faded)
                final = concatenate_videoclips(faded_clips)
            else:
                final = concatenate_videoclips(clips)

            video_codec, audio_codec = get_video_codecs(output_abspath)
            final.write_videofile(
                output_abspath, codec=video_codec, audio_codec=audio_codec
            )

            return final.duration
        finally:
            if final:
                final.close()
            for clip in faded_clips:
                clip.close()
            for clip in clips:
                clip.close()
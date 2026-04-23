def _extract_transcription(self, segments: list) -> list[str]:
        """Extract transcription parts from segments."""
        transcription_parts = []
        for segment in segments:
            if self.media_type == "audio" and "audio" in segment:
                transcription_parts.append(segment["audio"].get("content", ""))
            elif self.media_type == "video" and "video" in segment:
                transcription_parts.append(segment["video"].get("content", ""))
                # Also include audio if available for video
                if "audio" in segment:
                    audio_content = segment["audio"].get("content", "")
                    if audio_content and audio_content.strip():
                        transcription_parts.append(f"[Audio: {audio_content}]")
        return transcription_parts
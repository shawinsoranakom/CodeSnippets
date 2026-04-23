def _simulate_retry_loop(
        self,
        attempt_results: list[str],
        transcript_content: str = "some_content",
        compact_result: str | None = "compacted_content",
    ) -> dict:
        """Simulate the retry loop and return final state.

        Args:
            attempt_results: List of outcomes per attempt.
                "success" = stream completes normally
                "error"   = streaming error
            transcript_content: Initial transcript content ("" = none)
            compact_result: Result of compact_transcript (None = failure)
        """
        _stream_error: Exception | None = None
        skip_transcript_upload = False
        use_resume = bool(transcript_content)
        stream_completed = False
        attempts_made = 0
        _tried_compaction = False

        for _attempt in range(min(_MAX_STREAM_ATTEMPTS, len(attempt_results))):
            if _attempt > 0:
                _stream_error = None
                stream_completed = False

                # First retry: try compacting the transcript.
                # Subsequent retries: drop transcript, rebuild from DB.
                if transcript_content and not _tried_compaction:
                    _tried_compaction = True
                    if compact_result and compact_result != transcript_content:
                        use_resume = True
                    else:
                        use_resume = False
                        skip_transcript_upload = True
                else:
                    use_resume = False
                    skip_transcript_upload = True

            attempts_made += 1
            result = attempt_results[_attempt]

            if result == "error":
                _stream_error = Exception("simulated error")
                continue  # skip post-stream

            # Stream succeeded
            stream_completed = True
            break

        if _stream_error is not None:
            skip_transcript_upload = True

        return {
            "attempts_made": attempts_made,
            "stream_error": _stream_error,
            "skip_transcript_upload": skip_transcript_upload,
            "stream_completed": stream_completed,
            "use_resume": use_resume,
        }
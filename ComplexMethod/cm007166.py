def create_transcription_job(self) -> Data:
        aai.settings.api_key = self.api_key

        # Convert speakers_expected to int if it's not empty
        speakers_expected = None
        if self.speakers_expected and self.speakers_expected.strip():
            try:
                speakers_expected = int(self.speakers_expected)
            except ValueError:
                self.status = "Error: Expected Number of Speakers must be a valid integer"
                return Data(data={"error": "Error: Expected Number of Speakers must be a valid integer"})

        language_code = self.language_code or None

        config = aai.TranscriptionConfig(
            speech_model=self.speech_model,
            language_detection=self.language_detection,
            language_code=language_code,
            speaker_labels=self.speaker_labels,
            speakers_expected=speakers_expected,
            punctuate=self.punctuate,
            format_text=self.format_text,
        )

        audio = None
        if self.audio_file:
            if self.audio_file_url:
                logger.warning("Both an audio file an audio URL were specified. The audio URL was ignored.")

            # Check if the file exists
            if not Path(self.audio_file).exists():
                self.status = "Error: Audio file not found"
                return Data(data={"error": "Error: Audio file not found"})
            audio = self.audio_file
        elif self.audio_file_url:
            audio = self.audio_file_url
        else:
            self.status = "Error: Either an audio file or an audio URL must be specified"
            return Data(data={"error": "Error: Either an audio file or an audio URL must be specified"})

        try:
            transcript = aai.Transcriber().submit(audio, config=config)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error submitting transcription job", exc_info=True)
            self.status = f"An error occurred: {e}"
            return Data(data={"error": f"An error occurred: {e}"})

        if transcript.error:
            self.status = transcript.error
            return Data(data={"error": transcript.error})
        result = Data(data={"transcript_id": transcript.id})
        self.status = result
        return result
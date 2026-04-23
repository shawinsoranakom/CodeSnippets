def run_lemur(self) -> Data:
        """Use the LeMUR task endpoint to input the LLM prompt."""
        aai.settings.api_key = self.api_key

        if not self.transcription_result and not self.transcript_ids:
            error = "Either a Transcription Result or Transcript IDs must be provided"
            self.status = error
            return Data(data={"error": error})
        if self.transcription_result and self.transcription_result.data.get("error"):
            # error message from the previous step
            self.status = self.transcription_result.data["error"]
            return self.transcription_result
        if self.endpoint == "task" and not self.prompt:
            self.status = "No prompt specified for the task endpoint"
            return Data(data={"error": "No prompt specified"})
        if self.endpoint == "question-answer" and not self.questions:
            error = "No Questions were provided for the question-answer endpoint"
            self.status = error
            return Data(data={"error": error})

        # Check for valid transcripts
        transcript_ids = None
        if self.transcription_result and "id" in self.transcription_result.data:
            transcript_ids = [self.transcription_result.data["id"]]
        elif self.transcript_ids:
            transcript_ids = self.transcript_ids.split(",") or []
            transcript_ids = [t.strip() for t in transcript_ids]

        if not transcript_ids:
            error = "Either a valid Transcription Result or valid Transcript IDs must be provided"
            self.status = error
            return Data(data={"error": error})

        # Get TranscriptGroup and check if there is any error
        transcript_group = aai.TranscriptGroup(transcript_ids=transcript_ids)
        transcript_group, failures = transcript_group.wait_for_completion(return_failures=True)
        if failures:
            error = f"Getting transcriptions failed: {failures[0]}"
            self.status = error
            return Data(data={"error": error})

        for t in transcript_group.transcripts:
            if t.status == aai.TranscriptStatus.error:
                self.status = t.error
                return Data(data={"error": t.error})

        # Perform LeMUR action
        try:
            response = self.perform_lemur_action(transcript_group, self.endpoint)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error running LeMUR", exc_info=True)
            error = f"An Error happened: {e}"
            self.status = error
            return Data(data={"error": error})

        result = Data(data=response)
        self.status = result
        return result
def process(self, chunk_seconds: float, speech_probability: float | None) -> bool:
        """Process samples using external VAD.

        Returns False when command is done.
        """
        if self.timed_out:
            self.timed_out = False

        self._timeout_seconds_left -= chunk_seconds
        if self._timeout_seconds_left <= 0:
            _LOGGER.debug(
                "VAD end of speech detection timed out after %s seconds",
                self.timeout_seconds,
            )
            self.reset()
            self.timed_out = True
            return False

        if speech_probability is None:
            speech_probability = 0.0

        if not self.in_command:
            # Before command
            is_speech = speech_probability > self.before_command_speech_threshold
            if is_speech:
                self._reset_seconds_left = self.reset_seconds
                self._speech_seconds_left -= chunk_seconds
                if self._speech_seconds_left <= 0:
                    # Inside voice command
                    self.in_command = True
                    self._command_seconds_left = (
                        self.command_seconds - self.speech_seconds
                    )
                    self._silence_seconds_left = self.silence_seconds
                    _LOGGER.debug("Voice command started")
            else:
                # Reset if enough silence
                self._reset_seconds_left -= chunk_seconds
                if self._reset_seconds_left <= 0:
                    self._speech_seconds_left = self.speech_seconds
                    self._reset_seconds_left = self.reset_seconds
        else:
            # In command
            is_speech = speech_probability > self.in_command_speech_threshold
            if not is_speech:
                # Silence in command
                self._reset_seconds_left = self.reset_seconds
                self._silence_seconds_left -= chunk_seconds
                self._command_seconds_left -= chunk_seconds
                if (self._silence_seconds_left <= 0) and (
                    self._command_seconds_left <= 0
                ):
                    # Command finished successfully
                    self.reset()
                    _LOGGER.debug("Voice command finished")
                    return False
            else:
                # Speech in command.
                # Reset silence counter if enough speech.
                self._reset_seconds_left -= chunk_seconds
                self._command_seconds_left -= chunk_seconds
                if self._reset_seconds_left <= 0:
                    self._silence_seconds_left = self.silence_seconds
                    self._reset_seconds_left = self.reset_seconds

        return True
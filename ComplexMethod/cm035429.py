def _run_cmd_with_retry(
        self,
        cmd: str,
        error_context: str,
        max_retries: int = CMD_RETRY_MAX_ATTEMPTS,
    ) -> CmdOutputObservation:
        """Run command with exponential backoff retry on bash session timeout."""
        if not cmd or not cmd.strip():
            raise ValueError('Command cannot be empty')
        if max_retries < 1:
            raise ValueError('max_retries must be at least 1')

        last_obs: Observation | None = None

        for attempt in range(max_retries):
            obs = self.run(CmdRunAction(cmd))

            if isinstance(obs, CmdOutputObservation) and obs.exit_code == 0:
                if attempt > 0:
                    logger.info(f'Command succeeded after {attempt + 1} attempts')
                return obs

            last_obs = obs
            is_retryable = self._is_bash_session_timeout(obs)

            if is_retryable and attempt < max_retries - 1:
                delay = self._calculate_retry_delay(attempt)
                logger.warning(
                    f'Bash session busy, retrying in {delay:.1f}s '
                    f'(attempt {attempt + 1}/{max_retries})'
                )
                time.sleep(delay)
                continue

            break

        error_content = self._extract_error_content(last_obs)
        raise RuntimeError(f'{error_context}: {error_content}')
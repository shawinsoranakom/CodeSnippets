def __init__(self, ydl, target: str | None = None):
        self.ydl = ydl
        # For backwards compat, target needs to be treated as if it could be None
        self.requested_channel, sep, self.requested_tag = (target or self._channel).rpartition('@')
        # Check if requested_tag is actually the requested repo/channel
        if not sep and ('/' in self.requested_tag or self.requested_tag in self._update_sources):
            self.requested_channel = self.requested_tag
            self.requested_tag: str = None  # type: ignore (we set it later)
        elif not self.requested_channel:
            # User did not specify a channel, so we are requesting the default channel
            self.requested_channel = self._channel.partition('@')[0]

        # --update should not be treated as an exact tag request even if CHANNEL has a @tag
        self._exact = bool(target) and target != self._channel
        if not self.requested_tag:
            # User did not specify a tag, so we request 'latest' and track that no exact tag was passed
            self.requested_tag = 'latest'
            self._exact = False

        if '/' in self.requested_channel:
            # requested_channel is actually a repository
            self.requested_repo = self.requested_channel
            if not self.requested_repo.startswith('yt-dlp/') and self.requested_repo != self._origin:
                self.ydl.report_warning(
                    f'You are switching to an {self.ydl._format_err("unofficial", "red")} executable '
                    f'from {self.ydl._format_err(self.requested_repo, self.ydl.Styles.EMPHASIS)}. '
                    f'Run {self.ydl._format_err("at your own risk", "light red")}')
                self._block_restart('Automatically restarting into custom builds is disabled for security reasons')
        else:
            # Check if requested_channel resolves to a known repository or else raise
            self.requested_repo = self._update_sources.get(self.requested_channel)
            if not self.requested_repo:
                self._report_error(
                    f'Invalid update channel {self.requested_channel!r} requested. '
                    f'Valid channels are {", ".join(self._update_sources)}', True)

        self._identifier = f'{detect_variant()} {system_identifier()}'
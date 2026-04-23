def _create_ssl_context(self) -> ssl.SSLContext | None:
        context: ssl.SSLContext | None = None
        assert self.ssl_certificate is not None
        try:
            if self.ssl_profile == SSL_INTERMEDIATE:
                context = ssl_util.server_context_intermediate()
            else:
                context = ssl_util.server_context_modern()
            context.load_cert_chain(self.ssl_certificate, self.ssl_key)
        except OSError as error:
            if not self.hass.config.recovery_mode:
                raise HomeAssistantError(
                    f"Could not use SSL certificate from {self.ssl_certificate}:"
                    f" {error}"
                ) from error
            _LOGGER.error(
                "Could not read SSL certificate from %s: %s",
                self.ssl_certificate,
                error,
            )
            try:
                context = self._create_emergency_ssl_context()
            except OSError as error2:
                _LOGGER.error(
                    "Could not create an emergency self signed ssl certificate: %s",
                    error2,
                )
                context = None
            else:
                _LOGGER.critical(
                    "Home Assistant is running in recovery mode with an emergency self"
                    " signed ssl certificate because the configured SSL certificate was"
                    " not usable"
                )
                return context

        if self.ssl_peer_certificate:
            if context is None:
                raise HomeAssistantError(
                    "Failed to create ssl context, no fallback available because a peer"
                    " certificate is required."
                )

            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(self.ssl_peer_certificate)

        return context
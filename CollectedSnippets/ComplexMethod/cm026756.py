async def _handle_local_webhook(self, hass, webhook_id, request):
        """Handle an incoming local SDK message."""
        # Circular dep
        from . import smart_home  # noqa: PLC0415

        self._local_last_active = utcnow()

        # Check version local SDK.
        version = request.headers.get("HA-Cloud-Version")
        if not self._local_sdk_version_warn and (
            not version or AwesomeVersion(version) < LOCAL_SDK_MIN_VERSION
        ):
            _LOGGER.warning(
                (
                    "Local SDK version is too old (%s), check documentation on how to"
                    " update to the latest version"
                ),
                version,
            )
            self._local_sdk_version_warn = True

        payload = await request.json()

        if _LOGGER.isEnabledFor(logging.DEBUG):
            msgid = "<UNKNOWN>"
            if isinstance(payload, dict):
                msgid = payload.get("requestId")
            _LOGGER.debug(
                "Received local message %s from %s (JS %s)",
                msgid,
                request.remote,
                request.headers.get("HA-Cloud-Version", "unknown"),
            )

        if (agent_user_id := self.get_agent_user_id_from_webhook(webhook_id)) is None:
            # No agent user linked to this webhook, means that the user has somehow unregistered
            # removing webhook and stopping processing of this request.
            _LOGGER.error(
                (
                    "Cannot process request for webhook %s as no linked agent user is"
                    " found:\n%s\n"
                ),
                partial_redact(webhook_id),
                pprint.pformat(async_redact_msg(payload, agent_user_id)),
            )
            webhook.async_unregister(self.hass, webhook_id)
            return None

        if not self.enabled:
            return json_response(
                smart_home.api_disabled_response(payload, agent_user_id)
            )

        result = await smart_home.async_handle_message(
            self.hass,
            self,
            agent_user_id,
            self.get_local_user_id(webhook_id),
            payload,
            SOURCE_LOCAL,
        )

        if _LOGGER.isEnabledFor(logging.DEBUG):
            if isinstance(payload, dict):
                _LOGGER.debug("Responding to local message %s", msgid)
            else:
                _LOGGER.debug("Empty response to local message %s", msgid)

        return json_response(result)
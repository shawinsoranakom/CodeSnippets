async def _push_message(self, payload: dict[str, Any], **kwargs: Any) -> None:
        """Send the message."""

        timestamp = int(time.time())
        ttl = int(kwargs.get(ATTR_TTL, DEFAULT_TTL))
        priority: str = kwargs.get(ATTR_PRIORITY, DEFAULT_PRIORITY)
        if priority not in ["normal", "high"]:
            priority = DEFAULT_PRIORITY
        payload["timestamp"] = timestamp * 1000  # Javascript ms since epoch

        if not (targets := kwargs.get(ATTR_TARGET)):
            targets = self.registrations.keys()

        for target in list(targets):
            info = self.registrations.get(target)
            try:
                info = cast(Registration, REGISTER_SCHEMA(info))
            except vol.Invalid:
                _LOGGER.error(
                    "%s is not a valid HTML5 push notification target", target
                )
                continue
            subscription = info["subscription"]
            payload[ATTR_DATA][ATTR_JWT] = add_jwt(
                timestamp,
                target,
                payload[ATTR_TAG],
                subscription["keys"]["auth"],
            )

            webpusher = WebPusher(
                cast(dict[str, Any], info["subscription"]), aiohttp_session=self.session
            )

            endpoint = urlparse(subscription["endpoint"])
            vapid_claims = {
                "sub": f"mailto:{self._vapid_email}",
                "aud": f"{endpoint.scheme}://{endpoint.netloc}",
                "exp": timestamp + (VAPID_CLAIM_VALID_HOURS * 60 * 60),
            }
            vapid_headers = Vapid.from_string(self._vapid_prv).sign(vapid_claims)
            vapid_headers.update({"urgency": priority, "priority": priority})

            response = await webpusher.send_async(
                data=json.dumps(payload), headers=vapid_headers, ttl=ttl
            )

            if TYPE_CHECKING:
                assert not isinstance(response, str)

            if response.status == HTTPStatus.GONE:
                _LOGGER.info("Notification channel has expired")
                reg = self.registrations.pop(target)
                try:
                    await self.hass.async_add_executor_job(
                        save_json, self.registrations_json_path, self.registrations
                    )
                except HomeAssistantError:
                    self.registrations[target] = reg
                    _LOGGER.error("Error saving registration")
                else:
                    _LOGGER.info("Configuration saved")
            elif response.status >= HTTPStatus.BAD_REQUEST:
                _LOGGER.error(
                    "There was an issue sending the notification %s: %s",
                    response.status,
                    await response.text(),
                )
async def _webpush(
        self,
        message: str | None = None,
        timestamp: datetime | None = None,
        ttl: timedelta | None = None,
        urgency: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Shared internal helper to push messages."""
        payload: dict[str, Any] = kwargs

        if message is not None:
            payload["body"] = message

        payload.setdefault(ATTR_TAG, str(uuid.uuid4()))
        ts = int(timestamp.timestamp()) if timestamp else int(time.time())
        payload[ATTR_TIMESTAMP] = ts * 1000

        if ATTR_REQUIRE_INTERACTION in payload:
            payload["requireInteraction"] = payload.pop(ATTR_REQUIRE_INTERACTION)

        payload.setdefault(ATTR_DATA, {})
        payload[ATTR_DATA][ATTR_JWT] = add_jwt(
            ts,
            self.target,
            payload[ATTR_TAG],
            self.registration["subscription"]["keys"]["auth"],
        )

        endpoint = urlparse(self.registration["subscription"]["endpoint"])
        vapid_claims = {
            "sub": f"mailto:{self.config_entry.data[ATTR_VAPID_EMAIL]}",
            "aud": f"{endpoint.scheme}://{endpoint.netloc}",
            "exp": ts + (VAPID_CLAIM_VALID_HOURS * 60 * 60),
        }

        try:
            response = await webpush_async(
                cast(dict[str, Any], self.registration["subscription"]),
                json.dumps(payload),
                self.config_entry.data[ATTR_VAPID_PRV_KEY],
                vapid_claims,
                ttl=int(ttl.total_seconds()) if ttl is not None else DEFAULT_TTL,
                headers={"Urgency": urgency} if urgency else None,
                aiohttp_session=self.session,
            )
            cast(ClientResponse, response).raise_for_status()
        except WebPushException as e:
            if cast(ClientResponse, e.response).status == HTTPStatus.GONE:
                reg = self.registrations.pop(self.target)
                try:
                    await self.hass.async_add_executor_job(
                        save_json, self.json_path, self.registrations
                    )
                except HomeAssistantError:
                    self.registrations[self.target] = reg
                    _LOGGER.error("Error saving registration")

                self.async_write_ha_state()
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="channel_expired",
                    translation_placeholders={"target": self.target},
                ) from e

            _LOGGER.debug("Full exception", exc_info=True)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="request_error",
                translation_placeholders={"target": self.target},
            ) from e
        except ClientError as e:
            _LOGGER.debug("Full exception", exc_info=True)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="connection_error",
                translation_placeholders={"target": self.target},
            ) from e
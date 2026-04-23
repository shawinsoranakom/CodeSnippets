async def async_step_pubsub_subscription(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure and create Pub/Sub subscription."""
        if TYPE_CHECKING:
            assert self._admin_client
        errors = {}
        if user_input is not None:
            subscription_name = user_input[CONF_SUBSCRIPTION_NAME]
            if subscription_name == CREATE_NEW_SUBSCRIPTION_KEY:
                topic_name = self._data[CONF_TOPIC_NAME]
                subscription_name = _generate_subscription_id(
                    self._data[CONF_CLOUD_PROJECT_ID]
                )
                _LOGGER.debug(
                    "Creating subscription %s on topic %s",
                    subscription_name,
                    topic_name,
                )
                try:
                    await self._admin_client.create_subscription(
                        topic_name,
                        subscription_name,
                    )
                except ApiException as err:
                    _LOGGER.error("Error creatingPub/Sub subscription: %s", err)
                    errors["base"] = "pubsub_api_error"
                else:
                    user_input[CONF_SUBSCRIPTION_NAME] = subscription_name
            else:
                # The user created this subscription themselves so do not delete when removing the integration.
                user_input[CONF_SUBSCRIBER_ID_IMPORTED] = True

            if not errors:
                self._data.update(user_input)
                subscriber = api.new_subscriber_with_token(
                    self.hass,
                    self._data["token"]["access_token"],
                    self._data[CONF_PROJECT_ID],
                    subscription_name,
                )
                try:
                    device_manager = await subscriber.async_get_device_manager()
                except ApiException as err:
                    # Generating a user friendly home name is best effort
                    _LOGGER.debug("Error fetching structures: %s", err)
                else:
                    self._structure_config_title = generate_config_title(
                        device_manager.structures.values()
                    )
                return await self._async_finish()

        subscriptions = []
        try:
            eligible_subscriptions = (
                await self._admin_client.list_eligible_subscriptions(
                    expected_topic_name=self._data[CONF_TOPIC_NAME],
                )
            )
        except ApiException as err:
            _LOGGER.error(
                "Error talking to API to list eligible Pub/Sub subscriptions: %s", err
            )
            errors["base"] = "pubsub_api_error"
        else:
            subscriptions.extend(eligible_subscriptions.subscription_names)
        subscriptions.append(CREATE_NEW_SUBSCRIPTION_KEY)
        return self.async_show_form(
            step_id="pubsub_subscription",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SUBSCRIPTION_NAME,
                        default=next(iter(subscriptions)),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            translation_key="subscription_name",
                            mode=SelectSelectorMode.LIST,
                            options=subscriptions,
                        )
                    )
                }
            ),
            description_placeholders={
                "topic": self._data[CONF_TOPIC_NAME],
                "more_info_url": MORE_INFO_URL,
            },
            errors=errors,
        )
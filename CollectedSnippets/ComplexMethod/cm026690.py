async def async_step_channels(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select which channels to track."""
        if user_input:
            return self.async_create_entry(
                title=self._title,
                data=self._data,
                options=user_input,
            )
        youtube = await self.get_resource(self._data[CONF_TOKEN][CONF_ACCESS_TOKEN])

        # Get user's own channels
        own_channels = [
            channel
            async for channel in youtube.get_user_channels()
            if channel.snippet is not None
        ]
        if not own_channels:
            return self.async_abort(
                reason="no_channel",
                description_placeholders={"support_url": CHANNEL_CREATION_HELP_URL},
            )

        # Start with user's own channels
        selectable_channels = [
            SelectOptionDict(
                value=channel.channel_id,
                label=f"{channel.snippet.title} (Your Channel)",
            )
            for channel in own_channels
        ]

        # Add subscribed channels
        selectable_channels.extend(
            [
                SelectOptionDict(
                    value=subscription.snippet.channel_id,
                    label=subscription.snippet.title,
                )
                async for subscription in youtube.get_user_subscriptions()
            ]
        )

        if not selectable_channels:
            return self.async_abort(reason="no_subscriptions")
        return self.async_show_form(
            step_id="channels",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CHANNELS): SelectSelector(
                        SelectSelectorConfig(options=selectable_channels, multiple=True)
                    ),
                }
            ),
        )
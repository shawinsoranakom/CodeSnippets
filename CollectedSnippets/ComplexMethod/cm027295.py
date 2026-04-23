async def async_step_configure_stream(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the Axis device stream options."""
        if user_input is not None:
            return self.async_create_entry(data=self.config_entry.options | user_input)

        schema = {}

        vapix = self.hub.api.vapix

        # Stream profiles

        if vapix.stream_profiles or (
            (profiles := vapix.params.stream_profile_handler.get("0"))
            and profiles.max_groups > 0
        ):
            stream_profiles = [DEFAULT_STREAM_PROFILE]
            stream_profiles.extend(profile.name for profile in vapix.streaming_profiles)

            schema[
                vol.Optional(
                    CONF_STREAM_PROFILE, default=self.hub.config.stream_profile
                )
            ] = vol.In(stream_profiles)

        # Video sources

        if (
            properties := vapix.params.property_handler.get("0")
        ) and properties.image_number_of_views > 0:
            await vapix.params.image_handler.update()
            video_sources: dict[int | str, str] = {
                DEFAULT_VIDEO_SOURCE: DEFAULT_VIDEO_SOURCE
            }
            for idx, video_source in vapix.params.image_handler.items():
                if not video_source.enabled:
                    continue
                video_sources[int(idx) + 1] = video_source.name

            schema[
                vol.Optional(CONF_VIDEO_SOURCE, default=self.hub.config.video_source)
            ] = vol.In(video_sources)

        return self.async_show_form(
            step_id="configure_stream", data_schema=vol.Schema(schema)
        )
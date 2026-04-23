def fill_out_missing_chromecast_info(self, hass: HomeAssistant) -> ChromecastInfo:
        """Return a new ChromecastInfo object with missing attributes filled in.

        Uses blocking HTTP / HTTPS.
        """
        cast_info = self.cast_info
        if self.cast_info.cast_type is None or self.cast_info.manufacturer is None:
            # Uses legacy hass.data[DOMAIN] pattern
            # pylint: disable-next=hass-use-runtime-data
            unknown_models = hass.data[DOMAIN]["unknown_models"]
            if self.cast_info.model_name not in unknown_models:
                # Manufacturer and cast type is not available in mDNS data,
                # get it over HTTP
                cast_info = dial.get_cast_type(
                    cast_info,
                    zconf=ChromeCastZeroconf.get_zeroconf(),
                )
                unknown_models[self.cast_info.model_name] = (
                    cast_info.cast_type,
                    cast_info.manufacturer,
                )

                report_issue = (
                    "create a bug report at "
                    "https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue"
                    "+label%3A%22integration%3A+cast%22"
                )

                _LOGGER.info(
                    (
                        "Fetched cast details for unknown model '%s' manufacturer:"
                        " '%s', type: '%s'. Please %s"
                    ),
                    cast_info.model_name,
                    cast_info.manufacturer,
                    cast_info.cast_type,
                    report_issue,
                )
            else:
                cast_type, manufacturer = unknown_models[self.cast_info.model_name]
                cast_info = CastInfo(
                    cast_info.services,
                    cast_info.uuid,
                    cast_info.model_name,
                    cast_info.friendly_name,
                    cast_info.host,
                    cast_info.port,
                    cast_type,
                    manufacturer,
                )

        if not self.is_audio_group or self.is_dynamic_group is not None:
            # We have all information, no need to check HTTP API.
            return ChromecastInfo(cast_info=cast_info)

        # Fill out missing group information via HTTP API.
        is_dynamic_group = False
        http_group_status = None
        http_group_status = dial.get_multizone_status(
            # We pass services which will be used for the HTTP request, and we
            # don't care about the host in http_group_status.dynamic_groups so
            # we pass an empty string to simplify the code.
            "",
            services=self.cast_info.services,
            zconf=ChromeCastZeroconf.get_zeroconf(),
        )
        if http_group_status is not None:
            is_dynamic_group = any(
                g.uuid == self.cast_info.uuid for g in http_group_status.dynamic_groups
            )

        return ChromecastInfo(
            cast_info=cast_info,
            is_dynamic_group=is_dynamic_group,
        )
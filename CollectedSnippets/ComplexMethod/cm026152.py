async def _try_update(self, *, tries: int) -> None:
        """Get the latest data from maps.yandex.ru and update the states."""
        attrs: dict[str, Any] = {}
        closer_time = None
        try:
            yandex_reply = await self.requester.get_stop_info(self._stop_id)
        except (CaptchaError, NoSessionError) as ex:
            _LOGGER.error(
                "%s. You may need to disable the integration for some time",
                ex,
            )
            return
        try:
            data = yandex_reply["data"]
        except KeyError as key_error:
            _LOGGER.warning(
                (
                    "Exception KeyError was captured, missing key is %s. Yandex"
                    " returned: %s"
                ),
                key_error,
                yandex_reply,
            )
            if tries > 0:
                return
            await self.requester.set_new_session()
            await self._try_update(tries=tries + 1)
            return

        stop_name = data["name"]
        transport_list = data["transports"]
        for transport in transport_list:
            for thread in transport["threads"]:
                if "Events" not in thread["BriefSchedule"]:
                    continue
                if thread.get("noBoarding") is True:
                    continue
                for event in thread["BriefSchedule"]["Events"]:
                    # Railway route depends on the essential stops and
                    # can vary over time.
                    # City transport has the fixed name for the route
                    if "railway" in transport["Types"]:
                        route = " - ".join(
                            [x["name"] for x in thread["EssentialStops"]]
                        )
                    else:
                        route = transport["name"]

                    if self._routes and route not in self._routes:
                        # skip unnecessary route info
                        continue
                    if "Estimated" not in event and "Scheduled" not in event:
                        continue

                    departure = event.get("Estimated") or event["Scheduled"]
                    posix_time_next = int(departure["value"])
                    if closer_time is None or closer_time > posix_time_next:
                        closer_time = posix_time_next
                    if route not in attrs:
                        attrs[route] = []
                    attrs[route].append(departure["text"])
        attrs[STOP_NAME] = stop_name

        if closer_time is None:
            self._attr_native_value = None
        else:
            self._attr_native_value = dt_util.utc_from_timestamp(closer_time).replace(
                microsecond=0
            )
        self._attr_extra_state_attributes = attrs
async def update_states(self) -> None:
        """Call the API of the camera device to update the internal states."""
        wake: dict[int, bool] = {}
        now = time()
        for channel in self._api.stream_channels:
            # wake the battery cameras for a complete update
            if not self._api.supported(channel, "battery"):
                wake[channel] = True
            elif (
                (
                    not self._api.sleeping(channel)
                    and now - self.last_wake[channel]
                    > BATTERY_PASSIVE_WAKE_UPDATE_INTERVAL
                )
                or (now - self.last_wake[channel] > BATTERY_WAKE_UPDATE_INTERVAL)
                or (now - self.last_all_wake > BATTERY_ALL_WAKE_UPDATE_INTERVAL)
            ):
                # let a waking update coincide with the camera waking up by itself unless it did not wake for BATTERY_WAKE_UPDATE_INTERVAL
                wake[channel] = True
                self.last_wake[channel] = now
            else:
                wake[channel] = False

            # check privacy mode if enabled
            if self._api.baichuan.privacy_mode(channel):
                await self._api.baichuan.get_privacy_mode(channel)

        if all(wake.values()):
            self.last_all_wake = now

        if self._api.baichuan.privacy_mode():
            return  # API is shutdown, no need to check states

        await self._api.get_states(cmd_list=self.update_cmd, wake=wake)
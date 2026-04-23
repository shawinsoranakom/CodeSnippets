async def _update(self, update_types_sequence: Sequence[str]) -> None:
        """Private update method."""
        update_types = set(update_types_sequence)
        update_events = {}
        _LOGGER.debug("Updating %s", update_types)
        if (
            "queue" in update_types
        ):  # update queue, queue before player for async_play_media
            if queue := await self._api.get_request("queue"):
                update_events["queue"] = asyncio.Event()
                async_dispatcher_send(
                    self.hass,
                    SIGNAL_UPDATE_QUEUE.format(self._entry_id),
                    queue,
                    update_events["queue"],
                )
        # order of below don't matter
        if not {"outputs", "volume"}.isdisjoint(update_types):  # update outputs
            if outputs := await self._api.get_request("outputs"):
                outputs = outputs["outputs"]
                update_events["outputs"] = (
                    asyncio.Event()
                )  # only for master, zones should ignore
                async_dispatcher_send(
                    self.hass,
                    SIGNAL_UPDATE_OUTPUTS.format(self._entry_id),
                    outputs,
                    update_events["outputs"],
                )
                self._add_zones(outputs)
        if not {"database"}.isdisjoint(update_types):
            pipes, playlists = await asyncio.gather(
                self._api.get_pipes(), self._api.get_playlists()
            )
            update_events["database"] = asyncio.Event()
            async_dispatcher_send(
                self.hass,
                SIGNAL_UPDATE_DATABASE.format(self._entry_id),
                pipes,
                playlists,
                update_events["database"],
            )
        if not {"update", "config"}.isdisjoint(update_types):  # not supported
            _LOGGER.debug("update/config notifications neither requested nor supported")
        if not {"player", "options", "volume"}.isdisjoint(
            update_types
        ):  # update player
            if player := await self._api.get_request("player"):
                update_events["player"] = asyncio.Event()
                if update_events.get("queue"):
                    await update_events[
                        "queue"
                    ].wait()  # make sure queue done before player for async_play_media
                async_dispatcher_send(
                    self.hass,
                    SIGNAL_UPDATE_PLAYER.format(self._entry_id),
                    player,
                    update_events["player"],
                )
        if update_events:
            await asyncio.wait(
                [asyncio.create_task(event.wait()) for event in update_events.values()]
            )  # make sure callbacks done before update
            async_dispatcher_send(
                self.hass, SIGNAL_UPDATE_MASTER.format(self._entry_id), True
            )
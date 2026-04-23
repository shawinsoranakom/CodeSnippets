async def _async_update_entity_states(self) -> None:
        """Update the states of all the polling entities.

        To protect from flooding the executor, we will update async entities
        in parallel and other entities sequential.

        This method must be run in the event loop.
        """
        if self._process_updates is None:
            self._process_updates = asyncio.Lock()
        if self._process_updates.locked():
            self.logger.warning(
                "Updating %s %s took longer than the scheduled update interval %s",
                self.platform_name,
                self.domain,
                self.scan_interval,
            )
            return

        async with self._process_updates:
            if self._update_in_sequence or len(self.entities) <= 1:
                # If we know we will update sequentially, we want to avoid scheduling
                # the coroutines as tasks that will wait on the semaphore lock.
                for entity in list(self.entities.values()):
                    # If the entity is removed from hass during the previous
                    # entity being updated, we need to skip updating the
                    # entity.
                    if entity.should_poll and entity.hass:
                        await entity.async_update_ha_state(True)
                return

            if tasks := [
                create_eager_task(
                    entity.async_update_ha_state(True), loop=self.hass.loop
                )
                for entity in self.entities.values()
                if entity.should_poll
            ]:
                await asyncio.gather(*tasks)
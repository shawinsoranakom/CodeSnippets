async def async_device_update(self, warning: bool = True) -> None:
        """Process 'update' or 'async_update' from entity.

        This method is a coroutine.
        """
        if self._update_staged:
            return

        hass = self.hass
        assert hass is not None

        self._update_staged = True

        # Process update sequential
        if self.parallel_updates:
            await self.parallel_updates.acquire()

        if warning:
            update_warn = hass.loop.call_at(
                hass.loop.time() + SLOW_UPDATE_WARNING, self._async_slow_update_warning
            )

        try:
            if hasattr(self, "async_update"):
                await self.async_update()
            elif hasattr(self, "update"):
                await hass.async_add_executor_job(self.update)
            else:
                return
        finally:
            self._update_staged = False
            if warning:
                update_warn.cancel()
            if self.parallel_updates:
                self.parallel_updates.release()
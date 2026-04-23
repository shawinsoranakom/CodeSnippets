async def _async_extra_update(self) -> None:
        """Update state of device."""
        if not self.coordinator.is_on:
            if self._dmr_device and self._dmr_device.is_subscribed:
                await self._dmr_device.async_unsubscribe_services()
            return

        startup_tasks: list[asyncio.Task[Any]] = []

        if not self._app_list_event.is_set():
            startup_tasks.append(create_eager_task(self._async_startup_app_list()))

        if self._dmr_device and not self._dmr_device.is_subscribed:
            startup_tasks.append(create_eager_task(self._async_resubscribe_dmr()))
        if not self._dmr_device and self._ssdp_rendering_control_location:
            startup_tasks.append(create_eager_task(self._async_startup_dmr()))

        if startup_tasks:
            await asyncio.gather(*startup_tasks)
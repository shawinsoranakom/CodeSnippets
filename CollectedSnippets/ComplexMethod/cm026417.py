async def _async_discover_roombas(
    hass: HomeAssistant, host: str | None = None
) -> list[RoombaInfo]:
    discovered_hosts: set[str] = set()
    devices: list[RoombaInfo] = []
    discover_lock = hass.data.setdefault(ROOMBA_DISCOVERY_LOCK, asyncio.Lock())
    discover_attempts = HOST_ATTEMPTS if host else ALL_ATTEMPTS

    for attempt in range(discover_attempts + 1):
        async with discover_lock:
            discovery = _async_get_roomba_discovery()
            discovered: set[RoombaInfo] = set()
            try:
                if host:
                    device = await hass.async_add_executor_job(discovery.get, host)
                    if device:
                        discovered.add(device)
                else:
                    discovered = await hass.async_add_executor_job(discovery.get_all)
            except OSError:
                # Socket temporarily unavailable
                await asyncio.sleep(ROOMBA_WAKE_TIME * attempt)
                continue
            else:
                for device in discovered:
                    if device.ip in discovered_hosts:
                        continue
                    discovered_hosts.add(device.ip)
                    devices.append(device)
            finally:
                discovery.server_socket.close()

        if host and host in discovered_hosts:
            return devices

        await asyncio.sleep(ROOMBA_WAKE_TIME)

    return devices
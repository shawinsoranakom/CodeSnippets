async def scan(self, wait_for: int = 0, bcast_ifaces=None):
        """Search for devices, return mocked data."""
        self.scan_count += 1
        _LOGGER.info("CALLED SCAN %d TIMES", self.scan_count)

        mock_infos = [x.device_info for x in self.mock_devices]

        new_infos = []
        updated_infos = []
        for info in mock_infos:
            if not [i for i in self.last_mock_infos if info.mac == i.mac]:
                new_infos.append(info)
            else:
                last_info = next(i for i in self.last_mock_infos if info.mac == i.mac)
                if info.ip != last_info.ip:
                    updated_infos.append(info)

        self.last_mock_infos = mock_infos
        for listener in self._listeners:
            [await listener.device_found(x) for x in new_infos]
            [await listener.device_update(x) for x in updated_infos]

        if wait_for:
            await asyncio.sleep(wait_for)

        return new_infos
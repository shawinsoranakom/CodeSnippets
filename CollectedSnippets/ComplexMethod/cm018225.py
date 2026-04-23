async def broadcast_msg(self, wait_for: int = 0):
        """Search for devices, return mocked data."""

        mock_infos = self.mock_devices
        last_mock_infos = self.last_mock_infos

        new_infos = []
        updated_infos = []

        for info in mock_infos.values():
            uuid = info.uuid
            if uuid not in last_mock_infos:
                new_infos.append(info)
            else:
                last_info = self.last_mock_infos[uuid]
                if info.inner_ip != last_info.inner_ip:
                    updated_infos.append(info)

        self.last_mock_infos = mock_infos
        for listener in self._listeners:
            [await listener.device_found(x) for x in new_infos]
            [await listener.device_update(x) for x in updated_infos]

        if wait_for:
            await asyncio.sleep(wait_for)

        return new_infos
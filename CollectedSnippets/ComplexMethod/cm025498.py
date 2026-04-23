def update(self) -> None:
        """Get the latest data from rtorrent and updates the state."""
        multicall = xmlrpc.client.MultiCall(self.client)
        multicall.throttle.global_up.rate()
        multicall.throttle.global_down.rate()
        multicall.d.multicall2("", "main")
        multicall.d.multicall2("", "stopped")
        multicall.d.multicall2("", "complete")
        multicall.d.multicall2("", "seeding", "d.up.rate=")
        multicall.d.multicall2("", "leeching", "d.down.rate=")

        try:
            self.data = cast(RTorrentData, multicall())
            self._attr_available = True
        except (xmlrpc.client.ProtocolError, OSError) as ex:
            _LOGGER.error("Connection to rtorrent failed (%s)", ex)
            self._attr_available = False
            return

        upload = self.data[0]
        download = self.data[1]
        all_torrents = self.data[2]
        stopped_torrents = self.data[3]
        complete_torrents = self.data[4]
        up_torrents = self.data[5]
        down_torrents = self.data[6]

        uploading_torrents = 0
        for up_torrent in up_torrents:
            if up_torrent[0]:
                uploading_torrents += 1

        downloading_torrents = 0
        for down_torrent in down_torrents:
            if down_torrent[0]:
                downloading_torrents += 1

        active_torrents = uploading_torrents + downloading_torrents

        sensor_type = self.entity_description.key
        if sensor_type == SENSOR_TYPE_CURRENT_STATUS:
            if self.data:
                if upload > 0 and download > 0:
                    self._attr_native_value = "up_down"
                elif upload > 0 and download == 0:
                    self._attr_native_value = "seeding"
                elif upload == 0 and download > 0:
                    self._attr_native_value = "downloading"
                else:
                    self._attr_native_value = STATE_IDLE
            else:
                self._attr_native_value = None

        if self.data:
            if sensor_type == SENSOR_TYPE_DOWNLOAD_SPEED:
                self._attr_native_value = format_speed(download)
            elif sensor_type == SENSOR_TYPE_UPLOAD_SPEED:
                self._attr_native_value = format_speed(upload)
            elif sensor_type == SENSOR_TYPE_ALL_TORRENTS:
                self._attr_native_value = len(all_torrents)
            elif sensor_type == SENSOR_TYPE_STOPPED_TORRENTS:
                self._attr_native_value = len(stopped_torrents)
            elif sensor_type == SENSOR_TYPE_COMPLETE_TORRENTS:
                self._attr_native_value = len(complete_torrents)
            elif sensor_type == SENSOR_TYPE_UPLOADING_TORRENTS:
                self._attr_native_value = uploading_torrents
            elif sensor_type == SENSOR_TYPE_DOWNLOADING_TORRENTS:
                self._attr_native_value = downloading_torrents
            elif sensor_type == SENSOR_TYPE_ACTIVE_TORRENTS:
                self._attr_native_value = active_torrents
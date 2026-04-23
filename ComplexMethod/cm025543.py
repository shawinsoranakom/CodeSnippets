async def _update_stream_source(self, camera: Camera) -> None:
        """Update the stream source in go2rtc config if needed."""
        if not (stream_source := await camera.stream_source()):
            await self.teardown()
            raise HomeAssistantError("Camera has no stream source")

        if camera.platform.platform_name == "generic":
            # This is a workaround to use ffmpeg for generic cameras
            # A proper fix will be added in the future together with supporting multiple streams per camera
            stream_source = "ffmpeg:" + stream_source

        if not self.async_is_supported(stream_source):
            await self.teardown()
            raise HomeAssistantError("Stream source is not supported by go2rtc")

        camera_prefs = await get_dynamic_camera_stream_settings(
            self._hass, camera.entity_id
        )
        if camera_prefs.orientation is not Orientation.NO_TRANSFORM:
            # Camera orientation manually set by user
            if not stream_source.startswith(_FFMPEG):
                stream_source = _FFMPEG + ":" + stream_source
            stream_source += "#video=h264#audio=copy"
            match camera_prefs.orientation:
                case Orientation.MIRROR:
                    stream_source += "#raw=-vf hflip"
                case Orientation.ROTATE_180:
                    stream_source += "#rotate=180"
                case Orientation.FLIP:
                    stream_source += "#raw=-vf vflip"
                case Orientation.ROTATE_LEFT_AND_FLIP:
                    # Cannot use any filter when using raw one
                    stream_source += "#raw=-vf transpose=2,vflip"
                case Orientation.ROTATE_LEFT:
                    stream_source += "#rotate=-90"
                case Orientation.ROTATE_RIGHT_AND_FLIP:
                    # Cannot use any filter when using raw one
                    stream_source += "#raw=-vf transpose=1,vflip"
                case Orientation.ROTATE_RIGHT:
                    stream_source += "#rotate=90"

        streams = await self._rest_client.streams.list()

        if (stream := streams.get(camera.entity_id)) is None or not any(
            stream_source == producer.url for producer in stream.producers
        ):
            await self._rest_client.streams.add(
                camera.entity_id,
                [
                    stream_source,
                    # We are setting any ffmpeg rtsp related logs to debug
                    # Connection problems to the camera will be logged by the first stream
                    # Therefore setting it to debug will not hide any important logs
                    f"ffmpeg:{camera.entity_id}#audio=opus#query=log_level=debug",
                ],
            )
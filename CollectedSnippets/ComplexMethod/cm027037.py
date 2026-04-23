def _generate_image(self, width: int | None, height: int | None) -> None:
        """Generate the keyframe image.

        This is run in an executor thread, but since it is called within an
        the asyncio lock from the main thread, there will only be one entry
        at a time per instance.
        """

        if not (self._turbojpeg and self._packet and self._codec_context):
            return
        packet = self._packet
        self._packet = None
        for _ in range(2):  # Retry once if codec context needs to be flushed
            try:
                # decode packet (flush afterwards)
                frames = self._codec_context.decode(packet)
                for _i in range(2):
                    if frames:
                        break
                    frames = self._codec_context.decode(None)
                break
            except EOFError:
                _LOGGER.debug("Codec context needs flushing")
                self._codec_context.flush_buffers()
        else:
            _LOGGER.debug("Unable to decode keyframe")
            return
        if frames:
            frame = frames[0]
            if width and height:
                if self._dynamic_stream_settings.orientation >= 5:
                    frame = frame.reformat(width=height, height=width)
                else:
                    frame = frame.reformat(width=width, height=height)
            bgr_array = self.transform_image(
                frame.to_ndarray(format="bgr24"),
                self._dynamic_stream_settings.orientation,
            )
            self._image = bytes(self._turbojpeg.encode(bgr_array))
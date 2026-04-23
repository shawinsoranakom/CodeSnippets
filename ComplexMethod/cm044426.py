def _analyze_source(self) -> tuple[T.Generator[av.Packet, None, None] | None, Fraction]:
        """Analyze the source to obtain the audio packets and the frame rate

        Returns
        -------
        audio_packets
            A generator containing audio packets from the source video, if audio is to be muxed
            otherwise ``None``
        fps
            The framerate of the original video
        """
        src = T.cast("InputContainer", self._containers["src"])
        fps = src.streams.video[0].average_rate
        assert fps is not None
        logger.debug("[%s] Source fps: %s", self.__class__.__name__, fps)

        if not self._mux_audio:
            logger.debug("[%s] Not muxing audio due to input parameters", self.__class__.__name__)
            return None, fps

        audio = next((s for s in src.streams if s.type == "audio"), None)
        if audio is None:
            logger.warning("No audio stream could be found in the source video '%s'. Audio mux "
                           "will be disabled.", self._source_video)
            self._mux_audio = False
            return None, fps

        packets = (p for p in src.demux(audio) if p.dts is not None)
        logger.debug("[%s] Muxing audio from source: %s", self.__class__.__name__, packets)
        self._next_audio_packet = next(packets)
        logger.debug("[%s] Queued first audio packet: %s",
                     self.__class__.__name__, self._next_audio_packet)
        return packets, fps
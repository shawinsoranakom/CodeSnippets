async def start_stream(
        self, session_info: dict[str, Any], stream_config: dict[str, Any]
    ) -> bool:
        """Start a new stream with the given configuration."""
        _LOGGER.debug(
            "[%s] Starting stream with the following parameters: %s",
            session_info["id"],
            stream_config,
        )
        if not (input_source := await self._async_get_stream_source()):
            _LOGGER.error("Camera has no stream source")
            return False
        if "-i " not in input_source:
            input_source = "-i " + input_source
        video_profile = ""
        if self.config[CONF_VIDEO_CODEC] != "copy":
            video_profile = (
                "-profile:v "
                + self.config[CONF_VIDEO_PROFILE_NAMES][
                    int.from_bytes(stream_config["v_profile_id"], byteorder="big")
                ]
                + " "
            )
        audio_application = ""
        audio_frame_duration = ""
        if self.config[CONF_AUDIO_CODEC] == "libopus":
            audio_application = "-application lowdelay "
            audio_frame_duration = (
                f"-frame_duration {stream_config.get('a_packet_time', 20)} "
            )
        # Start audio proxy to convert Opus RTP timestamps from 48kHz
        # (FFmpeg's hardcoded Opus RTP clock rate per RFC 7587) to the
        # sample rate negotiated by HomeKit (typically 16kHz).
        # a_sample_rate is in kHz (e.g. 16 for 16000 Hz) from pyhap TLV.
        audio_proxy: AudioProxy | None = None
        if self.config[CONF_SUPPORT_AUDIO]:
            audio_proxy = AudioProxy(
                dest_addr=stream_config["address"],
                dest_port=stream_config["a_port"],
                srtp_key_b64=stream_config["a_srtp_key"],
                target_clock_rate=stream_config["a_sample_rate"] * 1000,
            )
            await audio_proxy.async_start()
            if not audio_proxy.local_port:
                _LOGGER.error(
                    "[%s] Audio proxy failed to start",
                    self.display_name,
                )
                await audio_proxy.async_stop()
                audio_proxy = None

        output_vars = stream_config.copy()
        output_vars.update(
            {
                "v_profile": video_profile,
                "v_bufsize": stream_config["v_max_bitrate"] * 4,
                "v_map": self.config[CONF_VIDEO_MAP],
                "v_pkt_size": self.config[CONF_VIDEO_PACKET_SIZE],
                "v_codec": self.config[CONF_VIDEO_CODEC],
                "a_bufsize": stream_config["a_max_bitrate"] * 4,
                "a_map": self.config[CONF_AUDIO_MAP],
                "a_pkt_size": self.config[CONF_AUDIO_PACKET_SIZE],
                "a_encoder": self.config[CONF_AUDIO_CODEC],
                "a_application": audio_application,
                "a_frame_duration": audio_frame_duration,
                "a_proxy_port": audio_proxy.local_port if audio_proxy else 0,
            }
        )
        output = VIDEO_OUTPUT.format(**output_vars)
        if self.config[CONF_SUPPORT_AUDIO]:
            output = output + " " + AUDIO_OUTPUT.format(**output_vars)
        _LOGGER.debug("FFmpeg output settings: %s", output)
        stream = HAFFmpeg(self._ffmpeg.binary)
        opened = await stream.open(
            cmd=[],
            input_source=input_source,
            output=output,
            extra_cmd="-hide_banner -nostats",
            stderr_pipe=True,
            stdout_pipe=False,
        )
        if not opened:
            _LOGGER.error("Failed to open ffmpeg stream")
            if audio_proxy:
                await audio_proxy.async_stop()
            return False

        _LOGGER.debug(
            "[%s] Started stream process - PID %d",
            session_info["id"],
            stream.process.pid,
        )

        session_info["stream"] = stream
        session_info[FFMPEG_PID] = stream.process.pid
        session_info[AUDIO_PROXY] = audio_proxy

        stderr_reader = await stream.get_reader(source=FFMPEG_STDERR)

        async def watch_session(_: Any) -> None:
            await self._async_ffmpeg_watch(session_info["id"])

        session_info[FFMPEG_LOGGER] = create_eager_task(
            self._async_log_stderr_stream(stderr_reader)
        )
        session_info[FFMPEG_WATCHER] = async_track_time_interval(
            self.hass,
            watch_session,
            FFMPEG_WATCH_INTERVAL,
        )

        return await self._async_ffmpeg_watch(session_info["id"])
def get_info(input_=None, print_=False, **kwargs):
        """Get video Info"""
        logger.debug("input_: %s, print_: %s, kwargs: %s", input_, print_, kwargs)
        input_ = input_ if isinstance(input_, str) else input_.path
        logger.debug("input: %s", input_)
        data: dict[str, list[dict[str, T.Any]]] = {}
        with av.open(input_, "r") as container:
            for stream in container.streams:
                info: dict[str, T.Any] = stream.metadata
                info["frames"] = stream.frames
                info["codec"] = stream.codec_context.name
                info["profile"] = stream.profile
                info["bitrate"] = stream.codec_context.bit_rate
                if stream.duration and stream.time_base:
                    info["duration"] = float(stream.duration * stream.time_base)
                if stream.type == "video":
                    codec = T.cast(av.VideoCodecContext, stream.codec_context)
                    if stream.average_rate:
                        info["fps"] = float(stream.average_rate)
                    info["pix_fmt"] = codec.pix_fmt
                    info["size"] = (codec.width, codec.height)
                data.setdefault(stream.type, []).append(info)

        logger.debug(data)
        if print_:
            logger.info("======== Video Info ========",)
            logger.info("path: %s", input_)
            for stream_type, info in data.items():
                logger.info("---- %s ----", stream_type)
                for idx, stream_data in enumerate(info):
                    logger.info("index: %s", idx)
                    for key, val in stream_data.items():
                        logger.info("  %s: %s", key, val)
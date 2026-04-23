def save_to(
        self,
        path: str | io.BytesIO,
        format: VideoContainer = VideoContainer.AUTO,
        codec: VideoCodec = VideoCodec.AUTO,
        metadata: Optional[dict] = None,
    ):
        if isinstance(self.__file, io.BytesIO):
            self.__file.seek(0)  # Reset the BytesIO object to the beginning
        with av.open(self.__file, mode='r') as container:
            container_format = container.format.name
            video_encoding = container.streams.video[0].codec.name if len(container.streams.video) > 0 else None
            reuse_streams = True
            if format != VideoContainer.AUTO and format not in container_format.split(","):
                reuse_streams = False
            if codec != VideoCodec.AUTO and codec != video_encoding and video_encoding is not None:
                reuse_streams = False
            if self.__start_time or self.__duration:
                reuse_streams = False

            if not reuse_streams:
                components = self.get_components_internal(container)
                video = VideoFromComponents(components)
                return video.save_to(
                    path, format=format, codec=codec, metadata=metadata
                )

            streams = container.streams

            open_kwargs = get_open_write_kwargs(path, container_format, format)
            with av.open(path, **open_kwargs) as output_container:
                # Copy over the original metadata
                for key, value in container.metadata.items():
                    if metadata is None or key not in metadata:
                        output_container.metadata[key] = value

                # Add our new metadata
                if metadata is not None:
                    for key, value in metadata.items():
                        if isinstance(value, str):
                            output_container.metadata[key] = value
                        else:
                            output_container.metadata[key] = json.dumps(value)

                # Add streams to the new container
                stream_map = {}
                for stream in streams:
                    if isinstance(stream, (av.VideoStream, av.AudioStream, SubtitleStream)):
                        out_stream = output_container.add_stream_from_template(template=stream, opaque=True)
                        stream_map[stream] = out_stream

                # Write packets to the new container
                for packet in container.demux():
                    if packet.stream in stream_map and packet.dts is not None:
                        packet.stream = stream_map[packet.stream]
                        output_container.mux(packet)
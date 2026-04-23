def save_to(
        self,
        path: str,
        format: VideoContainer = VideoContainer.AUTO,
        codec: VideoCodec = VideoCodec.AUTO,
        metadata: Optional[dict] = None,
    ):
        """Save the video to a file path or BytesIO buffer."""
        if format != VideoContainer.AUTO and format != VideoContainer.MP4:
            raise ValueError("Only MP4 format is supported for now")
        if codec != VideoCodec.AUTO and codec != VideoCodec.H264:
            raise ValueError("Only H264 codec is supported for now")
        extra_kwargs = {}
        if isinstance(format, VideoContainer) and format != VideoContainer.AUTO:
            extra_kwargs["format"] = format.value
        elif isinstance(path, io.BytesIO):
            # BytesIO has no file extension, so av.open can't infer the format.
            # Default to mp4 since that's the only supported format anyway.
            extra_kwargs["format"] = "mp4"
        with av.open(path, mode='w', options={'movflags': 'use_metadata_tags'}, **extra_kwargs) as output:
            # Add metadata before writing any streams
            if metadata is not None:
                for key, value in metadata.items():
                    output.metadata[key] = json.dumps(value)

            frame_rate = Fraction(round(self.__components.frame_rate * 1000), 1000)
            # Create a video stream
            video_stream = output.add_stream('h264', rate=frame_rate)
            video_stream.width = self.__components.images.shape[2]
            video_stream.height = self.__components.images.shape[1]
            video_stream.pix_fmt = 'yuv420p'

            # Create an audio stream
            audio_sample_rate = 1
            audio_stream: Optional[av.AudioStream] = None
            if self.__components.audio:
                audio_sample_rate = int(self.__components.audio['sample_rate'])
                waveform = self.__components.audio['waveform']
                waveform = waveform[0, :, :math.ceil((audio_sample_rate / frame_rate) * self.__components.images.shape[0])]
                layout = {1: 'mono', 2: 'stereo', 6: '5.1'}.get(waveform.shape[0], 'stereo')
                audio_stream = output.add_stream('aac', rate=audio_sample_rate, layout=layout)

            # Encode video
            for i, frame in enumerate(self.__components.images):
                img = (frame * 255).clamp(0, 255).byte().cpu().numpy() # shape: (H, W, 3)
                frame = av.VideoFrame.from_ndarray(img, format='rgb24')
                frame = frame.reformat(format='yuv420p')  # Convert to YUV420P as required by h264
                packet = video_stream.encode(frame)
                output.mux(packet)

            # Flush video
            packet = video_stream.encode(None)
            output.mux(packet)

            if audio_stream and self.__components.audio:
                frame = av.AudioFrame.from_ndarray(waveform.float().cpu().contiguous().numpy(), format='fltp', layout=layout)
                frame.sample_rate = audio_sample_rate
                frame.pts = 0
                output.mux(audio_stream.encode(frame))

                # Flush encoder
                output.mux(audio_stream.encode(None))
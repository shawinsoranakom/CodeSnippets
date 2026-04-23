def get_components_internal(self, container: InputContainer) -> VideoComponents:
        video_stream = self._get_first_video_stream(container)
        if self.__start_time < 0:
            start_time = max(self._get_raw_duration() + self.__start_time, 0)
        else:
            start_time = self.__start_time
        # Get video frames
        frames = []
        start_pts = int(start_time / video_stream.time_base)
        end_pts = int((start_time + self.__duration) / video_stream.time_base)
        container.seek(start_pts, stream=video_stream)
        for frame in container.decode(video_stream):
            if frame.pts < start_pts:
                continue
            if self.__duration and frame.pts >= end_pts:
                break
            img = frame.to_ndarray(format='rgb24')  # shape: (H, W, 3)
            img = torch.from_numpy(img) / 255.0  # shape: (H, W, 3)
            frames.append(img)

        images = torch.stack(frames) if len(frames) > 0 else torch.zeros(0, 3, 0, 0)

        # Get frame rate
        frame_rate = Fraction(video_stream.average_rate) if video_stream.average_rate else Fraction(1)

        # Get audio if available
        audio = None
        container.seek(start_pts, stream=video_stream)
        # Use last stream for consistency
        if len(container.streams.audio):
            audio_stream = container.streams.audio[-1]
            audio_frames = []
            resample = av.audio.resampler.AudioResampler(format='fltp').resample
            frames = itertools.chain.from_iterable(
                map(resample, container.decode(audio_stream))
            )

            has_first_frame = False
            for frame in frames:
                offset_seconds = start_time - frame.pts * audio_stream.time_base
                to_skip = max(0, int(offset_seconds * audio_stream.sample_rate))
                if to_skip < frame.samples:
                    has_first_frame = True
                    break
            if has_first_frame:
                audio_frames.append(frame.to_ndarray()[..., to_skip:])

            for frame in frames:
                if self.__duration and frame.time > start_time + self.__duration:
                    break
                audio_frames.append(frame.to_ndarray())  # shape: (channels, samples)
            if len(audio_frames) > 0:
                audio_data = np.concatenate(audio_frames, axis=1)  # shape: (channels, total_samples)
                if self.__duration:
                    audio_data = audio_data[..., :int(self.__duration * audio_stream.sample_rate)]

                audio_tensor = torch.from_numpy(audio_data).unsqueeze(0)  # shape: (1, channels, total_samples)
                audio = AudioInput({
                    "waveform": audio_tensor,
                    "sample_rate": int(audio_stream.sample_rate) if audio_stream.sample_rate else 1,
                })

        metadata = container.metadata
        return VideoComponents(images=images, audio=audio, frame_rate=frame_rate, metadata=metadata)
def _get_pts_and_keyframes(self) -> None:
        """Parse the video for Presentation Time Stamps and keyframes and populate to :attr:`_pts`
        and :attr:`_keyframes"""
        logger.debug("[%s] Parsing video for PTS and keyframes: '%s'",
                     self.__class__.__name__, self._video_file)
        pts: list[int] = []
        keyframes: list[int] = []
        with av.open(self._video_file, "r") as container:
            stream = self._get_stream(container)
            assert stream.time_base is not None

            p_bar = tqdm(desc="Analyzing Video", leave=False, total=self.duration, unit="secs")
            i = last_update = offset = 0
            decoder = container.decode(stream)
            while True:
                try:
                    frame = next(decoder)
                except StopIteration:
                    break
                except av.error.InvalidDataError:
                    logger.warning("Invalid data encountered at frame %s in video '%s'",
                                   i, self._video_file)
                    continue
                assert frame.pts is not None
                if i == 0:
                    offset = frame.pts
                pts.append(frame.pts)
                if frame.key_frame:  # pyright:ignore[reportAttributeAccessIssue]
                    keyframes.append(i)
                cur_sec = int((frame.pts - offset) * stream.time_base)
                i += 1
                if cur_sec == last_update:
                    continue
                p_bar.update(cur_sec - last_update)
                last_update = cur_sec
        self._pts = np.array(pts, dtype=np.int64)
        self._keyframes = np.array(keyframes, dtype=np.int64)
        logger.debug("[%s] '%s' frame_pts: %s, keyframes: %s, frame_count: %s",
                     self.__class__.__name__, self._video_file, pts, keyframes, len(pts))
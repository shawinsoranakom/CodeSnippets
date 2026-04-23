def _read_frames_with_recovery(
        cls,
        cap: "cv2.VideoCapture",
        frame_indices: list[int],
        total_frames: int,
    ) -> tuple[npt.NDArray, list[int], dict[int, int]]:
        """
        Read frames with dynamic window forward-scan recovery.

        When a target frame fails to load, the next successfully grabbed
        frame (before the next target frame) will be used to recover it.

        Args:
            cap: OpenCV VideoCapture object
            frame_indices: Sorted list of target frame indices to load
            total_frames: Total number of frames in the video

        Returns:
            Tuple of (frames_array, valid_frame_indices, recovered_map)
            - frames_array: Array of loaded frames
            - valid_frame_indices: List of frame indices that were loaded
            - recovered_map: Dict mapping recovered_idx -> source_idx
        """
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        assert width > 0 and height > 0, (
            f"Invalid video frame size: width={width}, height={height}"
        )

        frame_idx_set = set(frame_indices)
        max_frame_idx = frame_indices[-1] if frame_indices else 0

        # Build map: target_idx -> next_target_idx (for recovery window)
        next_target_map: dict[int, int] = {}
        for k in range(len(frame_indices) - 1):
            next_target_map[frame_indices[k]] = frame_indices[k + 1]
        next_target_map[frame_indices[-1]] = total_frames

        frames_list: list[npt.NDArray] = []
        valid_frame_indices: list[int] = []
        failed_frames_idx: list[int] = []
        recovered_map: dict[int, int] = {}

        i = 0
        for idx in range(max_frame_idx + 1):
            is_target_frame = idx in frame_idx_set

            # Attempt to grab the current frame
            ok = cap.grab()

            if not ok:
                if is_target_frame:
                    logger.warning(
                        "Failed to grab frame %d during video loading.",
                        idx,
                    )
                    failed_frames_idx.append(idx)
                continue

            # Check if we should retrieve: target frame OR can recover a failed one
            can_recover = cls._can_use_for_recovery(
                idx, failed_frames_idx, next_target_map, total_frames
            )

            if is_target_frame or can_recover:
                ret, frame = cap.retrieve()

                if ret and frame is not None and frame.size > 0:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames_list.append(rgb_frame)
                    valid_frame_indices.append(idx)
                    i += 1

                    if can_recover:
                        recovered_idx = failed_frames_idx.pop(0)
                        recovered_map[recovered_idx] = idx
                        logger.info(
                            "Recovered frame %d using frame %d (delay: %d)",
                            recovered_idx,
                            idx,
                            idx - recovered_idx,
                        )
                elif is_target_frame:
                    logger.warning(
                        "Failed to retrieve frame %d during video loading.",
                        idx,
                    )
                    failed_frames_idx.append(idx)

        # Log any remaining failed frames
        for failed_idx in failed_frames_idx:
            logger.warning(
                "Frame %d could not be recovered (end of video).",
                failed_idx,
            )

        # Stack frames
        if frames_list:
            frames = np.stack(frames_list)
        else:
            frames = np.empty((0, height, width, 3), dtype=np.uint8)

        return frames, valid_frame_indices, recovered_map
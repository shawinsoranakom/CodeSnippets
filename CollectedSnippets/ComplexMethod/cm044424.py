def count_frames(filename, fast=False):
    """ Count the number of frames in a video file

    There is no guaranteed accurate way to get a count of video frames without iterating through
    a video and decoding every frame.

    :func:`count_frames` can return an accurate count (albeit fairly slowly) or a possibly less
    accurate count, depending on the :attr:`fast` parameter. A progress bar is displayed.

    Parameters
    ----------
    filename: str
        Full path to the video to return the frame count from.
    fast: bool, optional
        Whether to count the frames without decoding them. This is significantly faster but
        accuracy is not guaranteed. Default: ``False``.

    Returns
    -------
    int:
        The number of frames in the given video file.

    Example
    -------
    >>> filename = "/path/to/video.mp4"
    >>> frame_count = count_frames(filename)
    """
    logger.debug("filename: %s, fast: %s", filename, fast)
    assert isinstance(filename, str), "Video path must be a string"
    cmd = [str(ffmpeg.FFMPEG_PATH), "-i", filename, "-map", "0:v:0"]
    if fast:
        cmd.extend(["-c", "copy"])
    cmd.extend(["-f", "null", "-"])

    logger.debug("FFMPEG Command: '%s'", " ".join(cmd))
    process = subprocess.Popen(cmd,
                               stderr=subprocess.STDOUT,
                               stdout=subprocess.PIPE,
                               universal_newlines=True, encoding="utf8")
    p_bar = None
    duration = None
    update = 0
    frames = 0
    stdout = process.stdout
    assert stdout is not None
    while True:

        output = stdout.readline().strip()
        if output == "" and process.poll() is not None:
            break

        if output.startswith("Duration:"):
            logger.debug("Duration line: %s", output)
            idx = output.find("Duration:") + len("Duration:")
            duration = int(convert_to_secs(*output[idx:].split(",", 1)[0].strip().split(":")))
            logger.debug("duration: %s", duration)
        if output.startswith("frame="):
            logger.debug("frame line: %s", output)
            if p_bar is None:
                logger.debug("Initializing tqdm")
                p_bar = tqdm(desc="Analyzing Video", leave=False, total=duration, unit="secs")
            time_idx = output.find("time=") + len("time=")
            frame_idx = output.find("frame=") + len("frame=")
            frames = int(output[frame_idx:].strip().split(" ")[0].strip())
            vid_time = int(convert_to_secs(*output[time_idx:].split(" ")[0].strip().split(":")))
            logger.debug("frames: %s, vid_time: %s", frames, vid_time)
            prev_update = update
            update = vid_time
            p_bar.update(update - prev_update)
    if p_bar is not None:
        p_bar.close()
    return_code = process.poll()
    logger.debug("Return code: %s, frames: %s", return_code, frames)
    return frames
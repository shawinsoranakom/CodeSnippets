def load_video(
    video: VideoInput,
    num_frames: int | None = None,
    fps: int | float | None = None,
    backend: str = "pyav",
    sample_indices_fn: Callable | None = None,
    **kwargs,
) -> np.ndarray:
    """
    Loads `video` to a numpy array.

    Args:
        video (`VideoInput`):
            The video to convert to the numpy array format. Can be a link to video or local path.
        num_frames (`int`, *optional*):
            Number of frames to sample uniformly. If not passed, the whole video is loaded.
        fps (`int` or `float`, *optional*):
            Number of frames to sample per second. Should be passed only when `num_frames=None`.
            If not specified and `num_frames==None`, all frames are sampled.
        backend (`str`, *optional*, defaults to `"pyav"`):
            The backend to use when loading the video. Can be any of ["decord", "pyav", "opencv", "torchvision", "torchcodec"]. Defaults to "pyav".
        sample_indices_fn (`Callable`, *optional*):
            A callable function that will return indices at which the video should be sampled. If the video has to be loaded using
            by a different sampling technique than provided by `num_frames` or `fps` arguments, one should provide their own `sample_indices_fn`.
            If not provided, simple uniformt sampling with fps is performed, otherwise `sample_indices_fn` has priority over other args.
            The function expects at input the all args along with all kwargs passed to `load_video` and should output valid
            indices at which the video should be sampled. For example:

            Example:
            def sample_indices_fn(metadata, **kwargs):
                return np.linspace(0, metadata.total_num_frames - 1, num_frames, dtype=int)

    Returns:
        tuple[`np.ndarray`, Dict]: A tuple containing:
            - Numpy array of frames in RGB (shape: [num_frames, height, width, 3]).
            - Metadata dictionary.
    """

    # If `sample_indices_fn` is given, we can accept any args as those might be needed by custom `sample_indices_fn`
    if fps is not None and num_frames is not None and sample_indices_fn is None:
        raise ValueError(
            "`num_frames`, `fps`, and `sample_indices_fn` are mutually exclusive arguments, please use only one!"
        )

    # If user didn't pass a sampling function, create one on the fly with default logic
    if sample_indices_fn is None:

        def sample_indices_fn_func(metadata, **fn_kwargs):
            return default_sample_indices_fn(metadata, num_frames=num_frames, fps=fps, **fn_kwargs)

        sample_indices_fn = sample_indices_fn_func

    # Early exit if provided an array or `PIL` frames
    if not isinstance(video, str):
        metadata = [None] * len(video)
        return video, metadata

    if urlparse(video).netloc in ["www.youtube.com", "youtube.com"]:
        if not is_yt_dlp_available():
            raise ImportError("To load a video from YouTube url you have  to install `yt_dlp` first.")
        # Lazy import from yt_dlp
        requires_backends(load_video, ["yt_dlp"])
        from yt_dlp import YoutubeDL

        buffer = BytesIO()
        with redirect_stdout(buffer), YoutubeDL() as f:
            f.download([video])
        bytes_obj = buffer.getvalue()
        file_obj = BytesIO(bytes_obj)
    elif video.startswith("http://") or video.startswith("https://"):
        file_obj = BytesIO(httpx.get(video, follow_redirects=True).content)
    elif os.path.isfile(video):
        file_obj = video
    else:
        raise TypeError("Incorrect format used for video. Should be an url linking to an video or a local path.")

    # can also load with decord, but not cv2/torchvision
    # both will fail in case of url links
    video_is_url = video.startswith("http://") or video.startswith("https://")
    if video_is_url and backend == "opencv":
        raise ValueError("If you are trying to load a video from URL, you cannot use 'opencv' as backend")

    if (
        (not is_decord_available() and backend == "decord")
        or (not is_av_available() and backend == "pyav")
        or (not is_cv2_available() and backend == "opencv")
        or (not is_torchvision_available() and backend == "torchvision")
        or (not is_torchcodec_available() and backend == "torchcodec")
    ):
        raise ImportError(
            f"You chose backend={backend} for loading the video but the required library is not found in your environment "
            f"Make sure to install {backend} before loading the video."
        )

    video_decoder = VIDEO_DECODERS[backend]
    video, metadata = video_decoder(file_obj, sample_indices_fn, **kwargs)
    return video, metadata
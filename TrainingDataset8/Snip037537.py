def marshall_video(
    coordinates: str,
    proto: VideoProto,
    data: MediaData,
    mimetype: str = "video/mp4",
    start_time: int = 0,
) -> None:
    """Marshalls a video proto, using url processors as needed.

    Parameters
    ----------
    coordinates : str
    proto : the proto to fill. Must have a string field called "data".
    data : str, bytes, BytesIO, numpy.ndarray, or file opened with
           io.open().
        Raw video data or a string with a URL pointing to the video
        to load. Includes support for YouTube URLs.
        If passing the raw data, this must include headers and any other
        bytes required in the actual file.
    mimetype : str
        The mime type for the video file. Defaults to 'video/mp4'.
        See https://tools.ietf.org/html/rfc4281 for more info.
    start_time : int
        The time from which this element should start playing. (default: 0)
    """

    proto.start_time = start_time

    # "type" distinguishes between YouTube and non-YouTube links
    proto.type = VideoProto.Type.NATIVE

    if isinstance(data, str) and url(data):
        youtube_url = _reshape_youtube_url(data)
        if youtube_url:
            proto.url = youtube_url
            proto.type = VideoProto.Type.YOUTUBE_IFRAME
        else:
            proto.url = data

    else:
        _marshall_av_media(coordinates, proto, data, mimetype)
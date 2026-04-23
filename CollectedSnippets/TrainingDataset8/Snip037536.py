def _marshall_av_media(
    coordinates: str,
    proto: Union[AudioProto, VideoProto],
    data: MediaData,
    mimetype: str,
) -> None:
    """Fill audio or video proto based on contents of data.

    Given a string, check if it's a url; if so, send it out without modification.
    Otherwise assume strings are filenames and let any OS errors raise.

    Load data either from file or through bytes-processing methods into a
    MediaFile object.  Pack proto with generated Tornado-based URL.

    (When running in "raw" mode, we won't actually load data into the
    MediaFileManager, and we'll return an empty URL.)
    """
    # Audio and Video methods have already checked if this is a URL by this point.

    if data is None:
        # Allow empty values so media players can be shown without media.
        return

    data_or_filename: Union[bytes, str]
    if isinstance(data, (str, bytes)):
        # Pass strings and bytes through unchanged
        data_or_filename = data
    elif isinstance(data, io.BytesIO):
        data.seek(0)
        data_or_filename = data.getvalue()
    elif isinstance(data, io.RawIOBase) or isinstance(data, io.BufferedReader):
        data.seek(0)
        read_data = data.read()
        if read_data is None:
            return
        else:
            data_or_filename = read_data
    elif type_util.is_type(data, "numpy.ndarray"):
        data_or_filename = data.tobytes()
    else:
        raise RuntimeError("Invalid binary data format: %s" % type(data))

    if runtime.exists():
        file_url = runtime.get_instance().media_file_mgr.add(
            data_or_filename, mimetype, coordinates
        )
        caching.save_media_data(data_or_filename, mimetype, coordinates)
    else:
        # When running in "raw mode", we can't access the MediaFileManager.
        file_url = ""

    proto.url = file_url
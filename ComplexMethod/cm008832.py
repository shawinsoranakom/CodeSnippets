def get_compatible_ext(*, vcodecs, acodecs, vexts, aexts, preferences=None):
    assert len(vcodecs) == len(vexts) and len(acodecs) == len(aexts)

    allow_mkv = not preferences or 'mkv' in preferences

    if allow_mkv and max(len(acodecs), len(vcodecs)) > 1:
        return 'mkv'  # TODO: any other format allows this?

    # TODO: All codecs supported by parse_codecs isn't handled here
    COMPATIBLE_CODECS = {
        'mp4': {
            'av1', 'hevc', 'avc1', 'mp4a', 'ac-4',  # fourcc (m3u8, mpd)
            'h264', 'aacl', 'ec-3',  # Set in ISM
        },
        'webm': {
            'av1', 'vp9', 'vp8', 'opus', 'vrbs',
            'vp9x', 'vp8x',  # in the webm spec
        },
    }

    sanitize_codec = functools.partial(
        try_get, getter=lambda x: x[0].split('.')[0].replace('0', '').lower())
    vcodec, acodec = sanitize_codec(vcodecs), sanitize_codec(acodecs)

    for ext in preferences or COMPATIBLE_CODECS.keys():
        codec_set = COMPATIBLE_CODECS.get(ext, set())
        if ext == 'mkv' or codec_set.issuperset((vcodec, acodec)):
            return ext

    COMPATIBLE_EXTS = (
        {'mp3', 'mp4', 'm4a', 'm4p', 'm4b', 'm4r', 'm4v', 'ismv', 'isma', 'mov'},
        {'webm', 'weba'},
    )
    for ext in preferences or vexts:
        current_exts = {ext, *vexts, *aexts}
        if ext == 'mkv' or current_exts == {ext} or any(
                ext_sets.issuperset(current_exts) for ext_sets in COMPATIBLE_EXTS):
            return ext
    return 'mkv' if allow_mkv else preferences[-1]
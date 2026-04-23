def parse_codecs(codecs_str):
    # http://tools.ietf.org/html/rfc6381
    if not codecs_str:
        return {}
    split_codecs = list(filter(None, map(
        lambda s: s.strip(), codecs_str.strip().split(','))))
    vcodec, acodec, hdr = None, None, None
    for full_codec in split_codecs:
        codec, rest = full_codec.partition('.')[::2]
        codec = codec.lower()
        full_codec = '.'.join((codec, rest)) if rest else codec
        codec = re.sub(r'0+(?=\d)', '', codec)
        if codec in ('avc1', 'avc2', 'avc3', 'avc4', 'vp9', 'vp8', 'hev1', 'hev2',
                     'h263', 'h264', 'mp4v', 'hvc1', 'av1', 'theora', 'dvh1', 'dvhe'):
            if vcodec:
                continue
            vcodec = full_codec
            if codec in ('dvh1', 'dvhe'):
                hdr = 'DV'
            elif codec in ('av1', 'vp9'):
                n, m = {
                    'av1': (2, '10'),
                    'vp9': (0, '2'),
                }[codec]
                if (rest.split('.', n + 1)[n:] or [''])[0].lstrip('0') == m:
                    hdr = 'HDR10'
        elif codec in ('flac', 'mp4a', 'opus', 'vorbis', 'mp3', 'aac', 'ac-4',
                       'ac-3', 'ec-3', 'eac3', 'dtsc', 'dtse', 'dtsh', 'dtsl'):
            if not acodec:
                acodec = full_codec
        else:
            write_string('WARNING: Unknown codec %s\n' % (full_codec,), sys.stderr)

    return (
        filter_dict({
            'vcodec': vcodec or 'none',
            'acodec': acodec or 'none',
            'dynamic_range': hdr,
        }) if vcodec or acodec
        else {
            'vcodec': split_codecs[0],
            'acodec': split_codecs[1],
        } if len(split_codecs) == 2
        else {})
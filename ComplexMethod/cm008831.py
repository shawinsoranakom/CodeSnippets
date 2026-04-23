def parse_codecs(codecs_str):
    # http://tools.ietf.org/html/rfc6381
    if not codecs_str:
        return {}
    split_codecs = list(filter(None, map(
        str.strip, codecs_str.strip().strip(',').split(','))))
    vcodec, acodec, scodec, hdr = None, None, None, None
    for full_codec in split_codecs:
        full_codec = re.sub(r'^([^.]+)', lambda m: m.group(1).lower(), full_codec)
        parts = re.sub(r'0+(?=\d)', '', full_codec).split('.')
        if parts[0] in ('avc1', 'avc2', 'avc3', 'avc4', 'vp9', 'vp8', 'hev1', 'hev2',
                        'h263', 'h264', 'mp4v', 'hvc1', 'av1', 'theora', 'dvh1', 'dvhe'):
            if vcodec:
                continue
            vcodec = full_codec
            if parts[0] in ('dvh1', 'dvhe'):
                hdr = 'DV'
            elif parts[0] == 'av1' and traversal.traverse_obj(parts, 3) == '10':
                hdr = 'HDR10'
            elif parts[:2] == ['vp9', '2']:
                hdr = 'HDR10'
        elif parts[0] in ('flac', 'mp4a', 'opus', 'vorbis', 'mp3', 'aac', 'ac-4',
                          'ac-3', 'ec-3', 'eac3', 'dtsc', 'dtse', 'dtsh', 'dtsl'):
            acodec = acodec or full_codec
        elif parts[0] in ('stpp', 'wvtt'):
            scodec = scodec or full_codec
        else:
            write_string(f'WARNING: Unknown codec {full_codec}\n')
    if vcodec or acodec or scodec:
        return {
            'vcodec': vcodec or 'none',
            'acodec': acodec or 'none',
            'dynamic_range': hdr,
            **({'scodec': scodec} if scodec is not None else {}),
        }
    elif len(split_codecs) == 2:
        return {
            'vcodec': split_codecs[0],
            'acodec': split_codecs[1],
        }
    return {}
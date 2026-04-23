def determine_protocol(info_dict):
    protocol = info_dict.get('protocol')
    if protocol is not None:
        return protocol

    url = sanitize_url(info_dict['url'])
    if url.startswith('rtmp'):
        return 'rtmp'
    elif url.startswith('mms'):
        return 'mms'
    elif url.startswith('rtsp'):
        return 'rtsp'

    ext = determine_ext(url)
    if ext == 'm3u8':
        return 'm3u8' if info_dict.get('is_live') else 'm3u8_native'
    elif ext == 'f4m':
        return 'f4m'

    return urllib.parse.urlparse(url).scheme
def _get_suitable_downloader(info_dict, params={}):
    """Get the downloader class that can handle the info dict."""

    # if (info_dict.get('start_time') or info_dict.get('end_time')) and not info_dict.get('requested_formats') and FFmpegFD.can_download(info_dict):
    #     return FFmpegFD

    external_downloader = params.get('external_downloader')
    if external_downloader is not None:
        ed = get_external_downloader(external_downloader)
        if ed.can_download(info_dict):
            return ed
        # Avoid using unwanted args since external_downloader was rejected
        if params.get('external_downloader_args'):
            params['external_downloader_args'] = None

    protocol = info_dict['protocol']
    if protocol.startswith('m3u8') and info_dict.get('is_live'):
        return FFmpegFD

    if protocol == 'm3u8' and params.get('hls_prefer_native') is True:
        return HlsFD

    if protocol == 'm3u8_native' and params.get('hls_prefer_native') is False:
        return FFmpegFD

    return PROTOCOL_MAP.get(protocol, HttpFD)
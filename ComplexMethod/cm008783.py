def _get_suitable_downloader(info_dict, protocol, params, default):
    """Get the downloader class that can handle the info dict."""
    if default is NO_DEFAULT:
        default = HttpFD

    if (info_dict.get('section_start') or info_dict.get('section_end')) and FFmpegFD.can_download(info_dict):
        return FFmpegFD

    info_dict['protocol'] = protocol
    downloaders = params.get('external_downloader')
    external_downloader = (
        downloaders if isinstance(downloaders, str) or downloaders is None
        else downloaders.get(shorten_protocol_name(protocol, True), downloaders.get('default')))

    if external_downloader is None:
        if info_dict['to_stdout'] and FFmpegFD.can_merge_formats(info_dict, params):
            return FFmpegFD
    elif external_downloader.lower() != 'native' and info_dict.get('impersonate') is None:
        ed = get_external_downloader(external_downloader)
        if ed.can_download(info_dict, external_downloader):
            return ed

    if protocol == 'http_dash_segments':
        if info_dict.get('is_live') and (external_downloader or '').lower() != 'native':
            return FFmpegFD

    if protocol in ('m3u8', 'm3u8_native'):
        if info_dict.get('is_live'):
            return FFmpegFD
        elif (external_downloader or '').lower() == 'native':
            return HlsFD
        elif protocol == 'm3u8_native' and get_suitable_downloader(
                info_dict, params, None, protocol='m3u8_frag_urls', to_stdout=info_dict['to_stdout']):
            return HlsFD
        elif params.get('hls_prefer_native') is True:
            return HlsFD
        elif params.get('hls_prefer_native') is False:
            return FFmpegFD

    return PROTOCOL_MAP.get(protocol, default)
def get_suitable_downloader(info_dict, params={}, default=NO_DEFAULT, protocol=None, to_stdout=False):
    info_dict['protocol'] = determine_protocol(info_dict)
    info_copy = info_dict.copy()
    info_copy['to_stdout'] = to_stdout

    protocols = (protocol or info_copy['protocol']).split('+')
    downloaders = [_get_suitable_downloader(info_copy, proto, params, default) for proto in protocols]

    if set(downloaders) == {FFmpegFD} and FFmpegFD.can_merge_formats(info_copy, params):
        return FFmpegFD
    elif (set(downloaders) == {DashSegmentsFD}
          and not (to_stdout and len(protocols) > 1)
          and set(protocols) == {'http_dash_segments_generator'}):
        return DashSegmentsFD
    elif len(downloaders) == 1:
        return downloaders[0]
    return None
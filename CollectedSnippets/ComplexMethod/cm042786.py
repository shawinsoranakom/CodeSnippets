def output(video_extractor, pretty_print=True):
    ve = video_extractor
    out = {}
    out['url'] = ve.url
    out['title'] = ve.title
    out['site'] = ve.name
    out['streams'] = ve.streams
    try:
        if ve.dash_streams:
            out['streams'].update(ve.dash_streams)
    except AttributeError:
        pass
    try:
        if ve.audiolang:
            out['audiolang'] = ve.audiolang
    except AttributeError:
        pass
    extra = {}
    if getattr(ve, 'referer', None) is not None:
        extra["referer"] = ve.referer
    if getattr(ve, 'ua', None) is not None:
        extra["ua"] = ve.ua
    if extra:
        out["extra"] = extra
    if pretty_print:
        print(json.dumps(out, indent=4, ensure_ascii=False))
    else:
        print(json.dumps(out))
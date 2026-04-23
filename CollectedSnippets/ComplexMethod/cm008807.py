def subs_list_to_dict(subs: list[dict] | None = None, /, *, lang='und', ext=None):
    """
    Convert subtitles from a traversal into a subtitle dict.
    The path should have an `all` immediately before this function.

    Arguments:
    `ext`      The default value for `ext` in the subtitle dict

    In the dict you can set the following additional items:
    `id`       The subtitle id to sort the dict into
    `quality`  The sort order for each subtitle
    """
    if subs is None:
        return functools.partial(subs_list_to_dict, lang=lang, ext=ext)

    result = collections.defaultdict(list)

    for sub in subs:
        if not url_or_none(sub.get('url')) and not sub.get('data'):
            continue
        sub_id = sub.pop('id', None)
        if not isinstance(sub_id, str):
            if not lang:
                continue
            sub_id = lang
        sub_ext = sub.get('ext')
        if not isinstance(sub_ext, str):
            if not ext:
                sub.pop('ext', None)
            else:
                sub['ext'] = ext
        result[sub_id].append(sub)
    result = dict(result)

    for subs in result.values():
        subs.sort(key=lambda x: x.pop('quality', 0) or 0)

    return result
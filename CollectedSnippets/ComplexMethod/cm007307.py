def subs_list_to_dict(subs, lang='und', ext=None):
    """
    Convert subtitles from a traversal into a subtitle dict.
    The path should have an `all` immediately before this function.

    Arguments:
    `lang`     The default language tag for subtitle dicts with no
               `lang` (`und`: undefined)
    `ext`      The default value for `ext` in the subtitle dicts

    In the dict you can set the following additional items:
    `id`       The language tag to which the subtitle dict should be added
    `quality`  The sort order for each subtitle dict
    """

    result = collections.defaultdict(list)

    for sub in subs:
        tn_url = url_or_none(sub.pop('url', None))
        if tn_url:
            sub['url'] = tn_url
        elif not sub.get('data'):
            continue
        sub_lang = sub.pop('id', None)
        if not isinstance(sub_lang, compat_str):
            if not lang:
                continue
            sub_lang = lang
        sub_ext = sub.get('ext')
        if not isinstance(sub_ext, compat_str):
            if not ext:
                sub.pop('ext', None)
            else:
                sub['ext'] = ext
        result[sub_lang].append(sub)
    result = dict(result)

    for subs in result.values():
        subs.sort(key=lambda x: x.pop('quality', 0) or 0)

    return result
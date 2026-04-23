def print_extractor_information(opts, urls):
    out = ''
    if opts.list_extractors:
        # Importing GenericIE is currently slow since it imports YoutubeIE
        from .extractor.generic import GenericIE

        urls = dict.fromkeys(urls, False)
        for ie in list_extractor_classes(opts.age_limit):
            out += ie.IE_NAME + (' (CURRENTLY BROKEN)' if not ie.working() else '') + '\n'
            if ie == GenericIE:
                matched_urls = [url for url, matched in urls.items() if not matched]
            else:
                matched_urls = tuple(filter(ie.suitable, urls.keys()))
                urls.update(dict.fromkeys(matched_urls, True))
            out += ''.join(f'  {url}\n' for url in matched_urls)
    elif opts.list_extractor_descriptions:
        _SEARCHES = ('cute kittens', 'slithering pythons', 'falling cat', 'angry poodle', 'purple fish', 'running tortoise', 'sleeping bunny', 'burping cow')
        out = '\n'.join(
            ie.description(markdown=False, search_examples=_SEARCHES)
            for ie in list_extractor_classes(opts.age_limit) if ie.working() and ie.IE_DESC is not False)
    elif opts.ap_list_mso:
        out = 'Supported TV Providers:\n{}\n'.format(render_table(
            ['mso', 'mso name'],
            [[mso_id, mso_info['name']] for mso_id, mso_info in MSO_INFO.items()]))
    else:
        return False
    write_string(out, out=sys.stdout)
    return True
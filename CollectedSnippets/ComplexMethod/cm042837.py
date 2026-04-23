def tudou_download_by_iid(iid, title, output_dir = '.', merge = True, info_only = False):
    data = json.loads(get_decoded_html('http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s' % iid))
    temp = max([data[i] for i in data if 'size' in data[i][0]], key=lambda x:sum([part['size'] for part in x]))
    vids, size = [t["k"] for t in temp], sum([t["size"] for t in temp])

    urls = []
    for vid in vids:
        for i in parseString(get_html('http://ct.v2.tudou.com/f?id=%s' % vid)).getElementsByTagName('f'):
            urls.append(i.firstChild.nodeValue.strip())

    ext = r1(r'http://[\w.]*/(\w+)/[\w.]*', urls[0])

    print_info(site_info, title, ext, size)
    if not info_only:
        download_urls(urls, title, ext, size, output_dir=output_dir, merge = merge)
def miaopai_download(url, output_dir='.', merge=False, info_only=False, **kwargs):
    if re.match(r'^http[s]://.*\.weibo\.com/\d+/.+', url):
        return miaopai_download_direct(url, info_only=info_only, output_dir=output_dir, merge=merge, **kwargs)

    if re.match(r'^http[s]://.*\.weibo\.(com|cn)/s/video/.+', url):
        return miaopai_download_story(url, info_only=info_only, output_dir=output_dir, merge=merge, **kwargs)

    # FIXME!
    if re.match(r'^http[s]://.*\.weibo\.com/tv/v/(\w+)', url):
        return miaopai_download_direct(url, info_only=info_only, output_dir=output_dir, merge=merge, **kwargs)

    if re.match(r'^http[s]://(.+\.)?weibo\.com/(tv/)?show/(\d{4}:\w+)', url):
        return miaopai_download_h5api(url, info_only=info_only, output_dir=output_dir, merge=merge, **kwargs)

    if re.match(r'^http[s]://(.+\.)?weibo\.com/show\?fid=(\d{4}:\w+)', url):
        return miaopai_download_h5api(url, info_only=info_only, output_dir=output_dir, merge=merge, **kwargs)

    fid = match1(url, r'\?fid=(\d{4}:\w+)')
    if fid is not None:
        miaopai_download_by_fid(fid, output_dir, merge, info_only)
    elif '/p/230444' in url:
        fid = match1(url, r'/p/230444(\w+)')
        miaopai_download_by_fid('1034:'+fid, output_dir, merge, info_only)
        pass
    else:
        mobile_page = get_content(url, headers = fake_headers_mobile)
        hit = re.search(r'"page_url"\s*:\s*"([^"]+)"', mobile_page)
        if not hit:
            raise Exception('Unknown pattern')
        else:
            escaped_url = hit.group(1)
            miaopai_download(urllib.parse.unquote(escaped_url), output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)
def baidu_pan_download(url):
    errno_patt = r'errno":([^"]+),'
    refer_url = ""
    fake_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'UTF-8,*;q=0.5',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Host': 'pan.baidu.com',
        'Origin': 'http://pan.baidu.com',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:13.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2500.0 Safari/537.36',
        'Referer': refer_url
    }
    if cookies:
        print('Use user specified cookies')
    else:
        print('Generating cookies...')
        fake_headers['Cookie'] = baidu_pan_gen_cookies(url)
    refer_url = "http://pan.baidu.com"
    html = get_content(url, fake_headers, decoded=True)
    isprotected = False
    sign, timestamp, bdstoken, appid, primary_id, fs_id, uk = baidu_pan_parse(
        html)
    if sign is None:
        if re.findall(r'\baccess-code\b', html):
            isprotected = True
            sign, timestamp, bdstoken, appid, primary_id, fs_id, uk, fake_headers, psk = baidu_pan_protected_share(
                url)
            # raise NotImplementedError("Password required!")
        if isprotected != True:
            raise AssertionError("Share not found or canceled: %s" % url)
    if bdstoken is None:
        bdstoken = ""
    if isprotected != True:
        sign, timestamp, bdstoken, appid, primary_id, fs_id, uk = baidu_pan_parse(
            html)
    request_url = "http://pan.baidu.com/api/sharedownload?sign=%s&timestamp=%s&bdstoken=%s&channel=chunlei&clienttype=0&web=1&app_id=%s" % (
        sign, timestamp, bdstoken, appid)
    refer_url = url
    post_data = {
        'encrypt': 0,
        'product': 'share',
        'uk': uk,
        'primaryid': primary_id,
        'fid_list': '[' + fs_id + ']'
    }
    if isprotected == True:
        post_data['sekey'] = psk
    response_content = post_content(request_url, fake_headers, post_data, True)
    errno = match1(response_content, errno_patt)
    if errno != "0":
        raise AssertionError(
            "Server refused to provide download link! (Errno:%s)" % errno)
    real_url = r1(r'dlink":"([^"]+)"', response_content).replace('\\/', '/')
    title = r1(r'server_filename":"([^"]+)"', response_content)
    assert real_url
    type, ext, size = url_info(real_url, faker=True)
    title_wrapped = json.loads('{"wrapper":"%s"}' % title)
    title = title_wrapped['wrapper']
    logging.debug(real_url)
    return real_url, title, ext, size
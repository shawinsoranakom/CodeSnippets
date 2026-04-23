def url_info(url, faker=False, headers={}):
    logging.debug('url_info: %s' % url)

    if faker:
        response = urlopen_with_retry(
            request.Request(url, headers=fake_headers)
        )
    elif headers:
        response = urlopen_with_retry(request.Request(url, headers=headers))
    else:
        response = urlopen_with_retry(request.Request(url))

    headers = response.headers

    type = headers['content-type']
    if type == 'image/jpg; charset=UTF-8' or type == 'image/jpg':
        type = 'audio/mpeg'  # fix for netease
    mapping = {
        'video/3gpp': '3gp',
        'video/f4v': 'flv',
        'video/mp4': 'mp4',
        'video/MP2T': 'ts',
        'video/quicktime': 'mov',
        'video/webm': 'webm',
        'video/x-flv': 'flv',
        'video/x-ms-asf': 'asf',
        'audio/mp4': 'mp4',
        'audio/mpeg': 'mp3',
        'audio/wav': 'wav',
        'audio/x-wav': 'wav',
        'audio/wave': 'wav',
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'application/pdf': 'pdf',
    }
    if type in mapping:
        ext = mapping[type]
    else:
        type = None
        if headers['content-disposition']:
            try:
                filename = parse.unquote(
                    r1(r'filename="?([^"]+)"?', headers['content-disposition'])
                )
                if len(filename.split('.')) > 1:
                    ext = filename.split('.')[-1]
                else:
                    ext = None
            except:
                ext = None
        else:
            ext = None

    if headers['transfer-encoding'] != 'chunked':
        size = headers['content-length'] and int(headers['content-length'])
    else:
        size = None

    return type, ext, size
def url_save(
    url, filepath, bar, refer=None, is_part=False, faker=False,
    headers=None, timeout=None, **kwargs
):
    tmp_headers = headers.copy() if headers is not None else {}
    # When a referer specified with param refer,
    # the key must be 'Referer' for the hack here
    if refer is not None:
        tmp_headers['Referer'] = refer
    if type(url) is list:
        chunk_sizes = [url_size(url, faker=faker, headers=tmp_headers) for url in url]
        file_size = sum(chunk_sizes)
        is_chunked, urls = True, url
    else:
        file_size = url_size(url, faker=faker, headers=tmp_headers)
        chunk_sizes = [file_size]
        is_chunked, urls = False, [url]

    continue_renameing = True
    while continue_renameing:
        continue_renameing = False
        if os.path.exists(filepath):
            if not force and (file_size == os.path.getsize(filepath) or skip_existing_file_size_check):
                if not is_part:
                    if bar:
                        bar.done()
                    if skip_existing_file_size_check:
                        log.w(
                            'Skipping {} without checking size: file already exists'.format(
                                tr(os.path.basename(filepath))
                            )
                        )
                    else:
                        log.w(
                            'Skipping {}: file already exists'.format(
                                tr(os.path.basename(filepath))
                            )
                        )
                else:
                    if bar:
                        bar.update_received(file_size)
                return
            else:
                if not is_part:
                    if bar:
                        bar.done()
                    if not force and auto_rename:
                        path, ext = os.path.basename(filepath).rsplit('.', 1)
                        finder = re.compile(r' \([1-9]\d*?\)$')
                        if (finder.search(path) is None):
                            thisfile = path + ' (1).' + ext
                        else:
                            def numreturn(a):
                                return ' (' + str(int(a.group()[2:-1]) + 1) + ').'
                            thisfile = finder.sub(numreturn, path) + ext
                        filepath = os.path.join(os.path.dirname(filepath), thisfile)
                        print('Changing name to %s' % tr(os.path.basename(filepath)), '...')
                        continue_renameing = True
                        continue
                    if log.yes_or_no('File with this name already exists. Overwrite?'):
                        log.w('Overwriting %s ...' % tr(os.path.basename(filepath)))
                    else:
                        return
        elif not os.path.exists(os.path.dirname(filepath)):
            os.mkdir(os.path.dirname(filepath))

    temp_filepath = filepath + '.download' if file_size != float('inf') \
        else filepath
    received = 0
    if not force:
        open_mode = 'ab'

        if os.path.exists(temp_filepath):
            received += os.path.getsize(temp_filepath)
            if bar:
                bar.update_received(os.path.getsize(temp_filepath))
    else:
        open_mode = 'wb'

    chunk_start = 0
    chunk_end = 0
    for i, url in enumerate(urls):
        received_chunk = 0
        chunk_start += 0 if i == 0 else chunk_sizes[i - 1]
        chunk_end += chunk_sizes[i]
        if received < file_size and received < chunk_end:
            if faker:
                tmp_headers = fake_headers
            '''
            if parameter headers passed in, we have it copied as tmp_header
            elif headers:
                headers = headers
            else:
                headers = {}
            '''
            if received:
                # chunk_start will always be 0 if not chunked
                tmp_headers['Range'] = 'bytes=' + str(received - chunk_start) + '-'
            if refer:
                tmp_headers['Referer'] = refer

            if timeout:
                response = urlopen_with_retry(
                    request.Request(url, headers=tmp_headers), timeout=timeout
                )
            else:
                response = urlopen_with_retry(
                    request.Request(url, headers=tmp_headers)
                )
            try:
                range_start = int(
                    response.headers[
                        'content-range'
                    ][6:].split('/')[0].split('-')[0]
                )
                end_length = int(
                    response.headers['content-range'][6:].split('/')[1]
                )
                range_length = end_length - range_start
            except:
                content_length = response.headers['content-length']
                range_length = int(content_length) if content_length is not None \
                    else float('inf')

            if is_chunked:  # always append if chunked
                open_mode = 'ab'
            elif file_size != received + range_length:  # is it ever necessary?
                received = 0
                if bar:
                    bar.received = 0
                open_mode = 'wb'

            with open(temp_filepath, open_mode) as output:
                while True:
                    buffer = None
                    try:
                        buffer = response.read(1024 * 256)
                    except socket.timeout:
                        pass
                    if not buffer:
                        if file_size == float('+inf'):  # Prevent infinite downloading
                            break
                        if is_chunked and received_chunk == range_length:
                            break
                        elif not is_chunked and received == file_size:  # Download finished
                            break
                        # Unexpected termination. Retry request
                        tmp_headers['Range'] = 'bytes=' + str(received - chunk_start) + '-'
                        response = urlopen_with_retry(
                            request.Request(url, headers=tmp_headers)
                        )
                        continue
                    output.write(buffer)
                    received += len(buffer)
                    received_chunk += len(buffer)
                    if bar:
                        bar.update_received(len(buffer))

    assert received == os.path.getsize(temp_filepath), '%s == %s == %s' % (
        received, os.path.getsize(temp_filepath), temp_filepath
    )

    if os.access(filepath, os.W_OK) and file_size != float('inf'):
        # on Windows rename could fail if destination filepath exists
        # we should simply choose a new name instead of brutal os.remove(filepath)
        filepath = filepath + " (2)"
    os.rename(temp_filepath, filepath)
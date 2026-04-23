def url_get(module, url, dest, use_proxy, last_mod_time, force, timeout=10, headers=None, tmp_dest='', method='GET', unredirected_headers=None,
            decompress=True, ciphers=None, use_netrc=True):
    """
    Download data from the url and store in a temporary file.

    Return (tempfile, info about the request)
    """

    start = datetime.now(timezone.utc)
    rsp, info = fetch_url(module, url, use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout, headers=headers, method=method,
                          unredirected_headers=unredirected_headers, decompress=decompress, ciphers=ciphers, use_netrc=use_netrc)
    elapsed = (datetime.now(timezone.utc) - start).seconds

    if info['status'] == 304:
        module.exit_json(url=url, dest=dest, changed=False, msg=info.get('msg', ''), status_code=info['status'], elapsed=elapsed)

    # Exceptions in fetch_url may result in a status -1, the ensures a proper error to the user in all cases
    if info['status'] == -1:
        module.fail_json(msg=info['msg'], url=url, dest=dest, elapsed=elapsed)

    if info['status'] != 200 and not url.startswith('file:/') and not (url.startswith('ftp:/') and info.get('msg', '').startswith('OK')):
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'], url=url, dest=dest, elapsed=elapsed)

    # create a temporary file and copy content to do checksum-based replacement
    if tmp_dest:
        # tmp_dest should be an existing dir
        tmp_dest_is_dir = os.path.isdir(tmp_dest)
        if not tmp_dest_is_dir:
            if os.path.exists(tmp_dest):
                module.fail_json(msg="%s is a file but should be a directory." % tmp_dest, elapsed=elapsed)
            else:
                module.fail_json(msg="%s directory does not exist." % tmp_dest, elapsed=elapsed)
    else:
        tmp_dest = module.tmpdir

    fd, tempname = tempfile.mkstemp(dir=tmp_dest)

    f = os.fdopen(fd, 'wb')
    try:
        shutil.copyfileobj(rsp, f)
    except Exception as e:
        os.remove(tempname)
        module.fail_json(msg="failed to create temporary content file: %s" % to_native(e), elapsed=elapsed)
    f.close()
    rsp.close()

    # Since shutil.copyfileobj() will read from HTTPResponse in chunks, HTTPResponse.read() will not recognize
    # if the entire content-length of data was not read. We need to do that validation here, unless a 'chunked'
    # transfer-encoding was used, in which case we will not know content-length because it will not be returned.
    # But in that case, HTTPResponse will behave correctly and recognize an IncompleteRead.

    is_gzip = info.get('content-encoding') == 'gzip'

    if not module.check_mode and 'content-length' in info:
        # If data is decompressed, then content-length won't match the amount of data we've read, so skip.
        if not is_gzip or (is_gzip and not decompress):
            st = os.stat(tempname)
            cl = int(info['content-length'])
            if st.st_size != cl:
                diff = cl - st.st_size
                module.fail_json(msg=f'Incomplete read, ({rsp.length=}, {cl=}, {st.st_size=}) failed to read remaining {diff} bytes')

    return tempname, info
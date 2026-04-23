def main():
    argument_spec = url_argument_spec()
    argument_spec['url']['required'] = True
    argument_spec.update(url_redirect_argument_spec())
    argument_spec.update(
        dest=dict(type='path'),
        url_username=dict(type='str', aliases=['user']),
        url_password=dict(type='str', aliases=['password'], no_log=True),
        body=dict(type='raw'),
        body_format=dict(type='str', default='raw', choices=['form-urlencoded', 'json', 'raw', 'form-multipart']),
        src=dict(type='path'),
        method=dict(type='str', default='GET'),
        return_content=dict(type='bool', default=False),
        follow_redirects=dict(type='str', default='safe', choices=['all', 'none', 'safe', 'urllib2']),
        creates=dict(type='path'),
        removes=dict(type='path'),
        status_code=dict(type='list', elements='int', default=[200]),
        timeout=dict(type='int', default=30),
        headers=dict(type='dict', default={}),
        unix_socket=dict(type='path'),
        remote_src=dict(type='bool', default=False),
        ca_path=dict(type='path', default=None),
        unredirected_headers=dict(type='list', elements='str', default=[]),
        decompress=dict(type='bool', default=True),
        ciphers=dict(type='list', elements='str'),
        use_netrc=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        add_file_common_args=True,
        mutually_exclusive=[['body', 'src']],
    )

    url = module.params['url']
    body = module.params['body']
    body_format = module.params['body_format'].lower()
    method = module.params['method'].upper()
    dest = module.params['dest']
    return_content = module.params['return_content']
    creates = module.params['creates']
    removes = module.params['removes']
    status_code = [int(x) for x in list(module.params['status_code'])]
    socket_timeout = module.params['timeout']
    ca_path = module.params['ca_path']
    dict_headers = module.params['headers']
    unredirected_headers = module.params['unredirected_headers']
    decompress = module.params['decompress']
    ciphers = module.params['ciphers']
    use_netrc = module.params['use_netrc']

    if not re.match('^[A-Z]+$', method):
        module.fail_json(msg="Parameter 'method' needs to be a single word in uppercase, like GET or POST.")

    if body_format == 'json':
        # Encode the body unless its a string, then assume it is pre-formatted JSON
        if not isinstance(body, str):
            body = json.dumps(body)
        if 'content-type' not in [header.lower() for header in dict_headers]:
            dict_headers['Content-Type'] = 'application/json'
    elif body_format == 'form-urlencoded':
        if not isinstance(body, str):
            try:
                body = form_urlencoded(body)
            except ValueError as e:
                module.fail_json(msg='failed to parse body as form_urlencoded: %s' % to_native(e), elapsed=0)
        if 'content-type' not in [header.lower() for header in dict_headers]:
            dict_headers['Content-Type'] = 'application/x-www-form-urlencoded'
    elif body_format == 'form-multipart':
        try:
            content_type, body = prepare_multipart(body)
        except (TypeError, ValueError) as e:
            module.fail_json(msg='failed to parse body as form-multipart: %s' % to_native(e))
        dict_headers['Content-Type'] = content_type

    if creates is not None:
        # do not run the command if the line contains creates=filename
        # and the filename already exists.  This allows idempotence
        # of uri executions.
        if os.path.exists(creates):
            module.exit_json(stdout="skipped, since '%s' exists" % creates, changed=False)

    if removes is not None:
        # do not run the command if the line contains removes=filename
        # and the filename does not exist.  This allows idempotence
        # of uri executions.
        if not os.path.exists(removes):
            module.exit_json(stdout="skipped, since '%s' does not exist" % removes, changed=False)

    # Make the request
    start = datetime.now(timezone.utc)
    r, info = uri(module, url, dest, body, body_format, method,
                  dict_headers, socket_timeout, ca_path, unredirected_headers,
                  decompress, ciphers, use_netrc)

    elapsed = (datetime.now(timezone.utc) - start).seconds

    if r and dest is not None and os.path.isdir(dest):
        filename = get_response_filename(r) or 'index.html'
        dest = os.path.join(dest, filename)

    if r and r.fp is not None:
        # r may be None for some errors
        # r.fp may be None depending on the error, which means there are no headers either
        content_type, main_type, sub_type, content_encoding = parse_content_type(r)
    else:
        content_type = 'application/octet-stream'
        main_type = 'application'
        sub_type = 'octet-stream'
        content_encoding = 'utf-8'

    if sub_type and '+' in sub_type:
        # https://www.rfc-editor.org/rfc/rfc6839#section-3.1
        sub_type_suffix = sub_type.partition('+')[2]
        maybe_json = content_type and sub_type_suffix.lower() in JSON_CANDIDATES
    elif sub_type:
        maybe_json = content_type and sub_type.lower() in JSON_CANDIDATES
    else:
        maybe_json = False

    maybe_output = maybe_json or return_content or info['status'] not in status_code

    if maybe_output:
        try:
            if r.fp is None or r.closed:
                raise TypeError
            content = r.read()
        except (AttributeError, TypeError):
            # there was no content, but the error read()
            # may have been stored in the info as 'body'
            content = info.pop('body', b'')
        except http.client.HTTPException as http_err:
            module.fail_json(msg=f"HTTP Error while fetching {url}: {to_native(http_err)}")
    elif r:
        content = r
    else:
        content = None

    resp = {}
    resp['redirected'] = info['url'] != url
    resp.update(info)

    resp['elapsed'] = elapsed
    resp['status'] = int(resp['status'])
    resp['changed'] = False

    # Write the file out if requested
    if r and dest is not None:
        if resp['status'] in status_code and resp['status'] != 304:
            write_file(module, dest, content, resp)
            # allow file attribute changes
            resp['changed'] = True
            module.params['path'] = dest
            file_args = module.load_file_common_arguments(module.params, path=dest)
            resp['changed'] = module.set_fs_attributes_if_different(file_args, resp['changed'])
        resp['path'] = dest

    # Transmogrify the headers, replacing '-' with '_', since variables don't
    # work with dashes.
    # In python3, the headers are title cased.  Lowercase them to be
    # compatible with the python2 behaviour.
    uresp = {}
    for key, value in resp.items():
        ukey = key.replace("-", "_").lower()
        uresp[ukey] = value

    if 'location' in uresp:
        uresp['location'] = urljoin(url, uresp['location'])

    # Default content_encoding to try
    if isinstance(content, bytes):
        u_content = to_text(content, encoding=content_encoding)
        if maybe_json:
            try:
                js = json.loads(u_content)
                uresp['json'] = js
            except Exception:
                ...
    else:
        u_content = None

    if module.no_log_values:
        uresp = sanitize_keys(uresp, module.no_log_values, NO_MODIFY_KEYS)

    if resp['status'] not in status_code:
        uresp['msg'] = 'Status code was %s and not %s: %s' % (resp['status'], status_code, uresp.get('msg', ''))
        if return_content:
            module.fail_json(content=u_content, **uresp)
        else:
            module.fail_json(**uresp)
    elif return_content:
        module.exit_json(content=u_content, **uresp)
    else:
        module.exit_json(**uresp)
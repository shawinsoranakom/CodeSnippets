def main():
    argument_spec = url_argument_spec()

    # setup aliases
    argument_spec['url_username']['aliases'] = ['username']
    argument_spec['url_password']['aliases'] = ['password']

    argument_spec.update(
        url=dict(type='str', required=True),
        dest=dict(type='path', required=True),
        backup=dict(type='bool', default=False),
        checksum=dict(type='str', default=''),
        timeout=dict(type='int', default=10),
        headers=dict(type='dict'),
        tmp_dest=dict(type='path'),
        unredirected_headers=dict(type='list', elements='str', default=[]),
        decompress=dict(type='bool', default=True),
        ciphers=dict(type='list', elements='str'),
        use_netrc=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=argument_spec,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    url = module.params['url']
    dest = module.params['dest']
    backup = module.params['backup']
    force = module.params['force']
    checksum = module.params['checksum']
    use_proxy = module.params['use_proxy']
    timeout = module.params['timeout']
    headers = module.params['headers']
    tmp_dest = module.params['tmp_dest']
    unredirected_headers = module.params['unredirected_headers']
    decompress = module.params['decompress']
    ciphers = module.params['ciphers']
    use_netrc = module.params['use_netrc']

    result = dict(
        changed=False,
        checksum_dest=None,
        checksum_src=None,
        dest=dest,
        elapsed=0,
        url=url,
    )

    dest_is_dir = os.path.isdir(dest)
    last_mod_time = None

    # checksum specified, parse for algorithm and checksum
    if checksum:
        try:
            algorithm, checksum = checksum.split(':', 1)
        except ValueError:
            module.fail_json(msg="The checksum parameter has to be in format <algorithm>:<checksum>", **result)

        if is_url(checksum):
            checksum_url = checksum
            # download checksum file to checksum_tmpsrc
            checksum_tmpsrc, _dummy = url_get(module, checksum_url, dest, use_proxy, last_mod_time, force, timeout, headers, tmp_dest,
                                              unredirected_headers=unredirected_headers, ciphers=ciphers, use_netrc=use_netrc)
            with open(checksum_tmpsrc) as f:
                lines = [line.rstrip('\n') for line in f]
            os.remove(checksum_tmpsrc)
            filename = url_filename(url)
            checksum_map = parse_digest_lines(filename=filename, lines=lines)
            # Look through each line in the checksum file for a hash corresponding to
            # the filename in the url, returning the first hash that is found.
            for cksum in (s for (s, f) in checksum_map if f == filename):
                checksum = cksum
                break
            else:
                checksum = None

            if checksum is None:
                module.fail_json(msg="Unable to find a checksum for file '%s' in '%s'" % (filename, checksum_url))
        # Remove any non-alphanumeric characters, including the infamous
        # Unicode zero-width space
        checksum = re.sub(r'\W+', '', checksum).lower()
        # Ensure the checksum portion is a hexdigest
        try:
            int(checksum, 16)
        except ValueError:
            module.fail_json(msg='The checksum format is invalid', **result)

    if not dest_is_dir and os.path.exists(dest):
        checksum_mismatch = False

        # If the download is not forced and there is a checksum, allow
        # checksum match to skip the download.
        if not force and checksum != '':
            destination_checksum = module.digest_from_file(dest, algorithm)

            if checksum != destination_checksum:
                checksum_mismatch = True

        # Not forcing redownload, unless checksum does not match
        if not force and checksum and not checksum_mismatch:
            # Not forcing redownload, unless checksum does not match
            # allow file attribute changes
            file_args = module.load_file_common_arguments(module.params, path=dest)
            result['changed'] = module.set_fs_attributes_if_different(file_args, False)
            if result['changed']:
                module.exit_json(msg="file already exists but file attributes changed", **result)
            module.exit_json(msg="file already exists", **result)

        # If the file already exists, prepare the last modified time for the
        # request.
        mtime = os.path.getmtime(dest)
        last_mod_time = datetime.fromtimestamp(mtime, timezone.utc)

        # If the checksum does not match we have to force the download
        # because last_mod_time may be newer than on remote
        if checksum_mismatch:
            force = True

    # download to tmpsrc
    start = datetime.now(timezone.utc)
    method = 'HEAD' if module.check_mode else 'GET'
    tmpsrc, info = url_get(module, url, dest, use_proxy, last_mod_time, force, timeout, headers, tmp_dest, method,
                           unredirected_headers=unredirected_headers, decompress=decompress, ciphers=ciphers, use_netrc=use_netrc)
    result['elapsed'] = (datetime.now(timezone.utc) - start).seconds
    result['src'] = tmpsrc

    # Now the request has completed, we can finally generate the final
    # destination file name from the info dict.

    if dest_is_dir:
        filename = extract_filename_from_headers(info)
        if not filename:
            # Fall back to extracting the filename from the URL.
            # Pluck the URL from the info, since a redirect could have changed
            # it.
            filename = url_filename(info['url'])
        dest = os.path.join(dest, filename)
        result['dest'] = dest

    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        os.remove(tmpsrc)
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'], **result)
    if not os.access(tmpsrc, os.R_OK):
        os.remove(tmpsrc)
        module.fail_json(msg="Source %s is not readable" % (tmpsrc), **result)
    result['checksum_src'] = module.sha1(tmpsrc)

    # check if there is no dest file
    if os.path.exists(dest):
        # raise an error if copy has no permission on dest
        if not os.access(dest, os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not writable" % (dest), **result)
        if not os.access(dest, os.R_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not readable" % (dest), **result)
        result['checksum_dest'] = module.sha1(dest)
    else:
        if not os.path.exists(os.path.dirname(dest)):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s does not exist" % (os.path.dirname(dest)), **result)
        if not os.access(os.path.dirname(dest), os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not writable" % (os.path.dirname(dest)), **result)

    if module.check_mode:
        if os.path.exists(tmpsrc):
            os.remove(tmpsrc)
        result['changed'] = ('checksum_dest' not in result or
                             result['checksum_src'] != result['checksum_dest'])
        module.exit_json(msg=info.get('msg', ''), **result)

    # If a checksum was provided, ensure that the temporary file matches this checksum
    # before moving it to the destination.
    if checksum != '':
        tmpsrc_checksum = module.digest_from_file(tmpsrc, algorithm)

        if checksum != tmpsrc_checksum:
            os.remove(tmpsrc)
            module.fail_json(msg=f"The checksum for {tmpsrc} did not match {checksum}; it was {tmpsrc_checksum}.", **result)

    # Copy temporary file to destination if necessary
    backup_file = None
    if result['checksum_src'] != result['checksum_dest']:
        try:
            if backup:
                if os.path.exists(dest):
                    backup_file = module.backup_local(dest)
            module.atomic_move(tmpsrc, dest, unsafe_writes=module.params['unsafe_writes'])
        except Exception as e:
            if os.path.exists(tmpsrc):
                os.remove(tmpsrc)
            module.fail_json(msg="failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(e)), **result)
        result['changed'] = True
    else:
        result['changed'] = False
        if os.path.exists(tmpsrc):
            os.remove(tmpsrc)

    # allow file attribute changes
    file_args = module.load_file_common_arguments(module.params, path=dest)
    result['changed'] = module.set_fs_attributes_if_different(file_args, result['changed'])

    # Backwards compat only.  We'll return None on FIPS enabled systems
    try:
        result['md5sum'] = module.md5(dest)
    except ValueError:
        result['md5sum'] = None

    if backup_file:
        result['backup_file'] = backup_file

    # Mission complete
    module.exit_json(msg=info.get('msg', ''), status_code=info.get('status', ''), **result)
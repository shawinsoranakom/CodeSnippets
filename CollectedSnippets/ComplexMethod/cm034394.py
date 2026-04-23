def main():
    module = AnsibleModule(
        argument_spec=dict(
            id=dict(type='str'),
            url=dict(type='str'),
            data=dict(type='str'),
            file=dict(type='path'),
            keyring=dict(type='path'),
            validate_certs=dict(type='bool', default=True),
            keyserver=dict(type='str'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True,
        mutually_exclusive=(('data', 'file', 'keyserver', 'url'),),
    )

    # parameters
    key_id = module.params['id']
    url = module.params['url']
    data = module.params['data']
    filename = module.params['file']
    keyring = module.params['keyring']
    state = module.params['state']
    keyserver = module.params['keyserver']

    # internal vars
    short_format = False
    short_key_id = None
    fingerprint = None
    error_no_error = "apt-key did not return an error, but %s (check that the id is correct and *not* a subkey)"

    # ensure we have requirements met
    find_needed_binaries(module)

    # initialize result dict
    r = {'changed': False}

    if not key_id:

        if keyserver:
            module.fail_json(msg="Missing key_id, required with keyserver.")

        if url:
            data = download_key(module, url)

        if filename:
            key_id = get_key_id_from_file(module, filename)
        elif data:
            key_id = get_key_id_from_data(module, data)

    r['id'] = key_id
    try:
        short_key_id, fingerprint, key_id = parse_key_id(key_id)
        r['short_id'] = short_key_id
        r['fp'] = fingerprint
        r['key_id'] = key_id
    except ValueError:
        module.fail_json(msg='Invalid key_id', **r)

    if not fingerprint:
        # invalid key should fail well before this point, but JIC ...
        module.fail_json(msg="Unable to continue as we could not extract a valid fingerprint to compare against existing keys.", **r)

    if len(key_id) == 8:
        short_format = True

    # get existing keys to verify if we need to change
    r['before'] = keys = all_keys(module, keyring, short_format)
    keys2 = []

    if state == 'present':
        if (short_format and short_key_id not in keys) or (not short_format and fingerprint not in keys):
            r['changed'] = True
            if not module.check_mode:
                if filename:
                    add_key(module, filename, keyring)
                elif keyserver:
                    import_key(module, keyring, keyserver, key_id)
                elif data:
                    # this also takes care of url if key_id was not provided
                    add_key(module, "-", keyring, data)
                elif url:
                    # we hit this branch only if key_id is supplied with url
                    data = download_key(module, url)
                    add_key(module, "-", keyring, data)
                else:
                    module.fail_json(msg="No key to add ... how did i get here?!?!", **r)

                # verify it got added
                r['after'] = keys2 = all_keys(module, keyring, short_format)
                if (short_format and short_key_id not in keys2) or (not short_format and fingerprint not in keys2):
                    module.fail_json(msg=error_no_error % 'failed to add the key', **r)

    elif state == 'absent':
        if not key_id:
            module.fail_json(msg="key is required to remove a key", **r)
        if fingerprint in keys:
            r['changed'] = True
            if not module.check_mode:
                # we use the "short" id: key_id[-8:], short_format=True
                # it's a workaround for https://bugs.launchpad.net/ubuntu/+source/apt/+bug/1481871
                if short_key_id is not None and remove_key(module, short_key_id, keyring):
                    r['after'] = keys2 = all_keys(module, keyring, short_format)
                    if fingerprint in keys2:
                        module.fail_json(msg=error_no_error % 'the key was not removed', **r)
                else:
                    module.fail_json(msg="error removing key_id", **r)

    module.exit_json(**r)
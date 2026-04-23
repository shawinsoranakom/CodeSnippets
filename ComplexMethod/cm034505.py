def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            src=dict(type='path', required=True),
            dest=dict(type='path', required=True),
            remote_src=dict(type='bool', default=False),
            creates=dict(type='path'),
            list_files=dict(type='bool', default=False),
            keep_newer=dict(type='bool', default=False),
            exclude=dict(type='list', elements='str', default=[]),
            include=dict(type='list', elements='str', default=[]),
            extra_opts=dict(type='list', elements='str', default=[]),
            validate_certs=dict(type='bool', default=True),
            io_buffer_size=dict(type='int', default=64 * 1024),

            # Options that are for the action plugin, but ignored by the module itself.
            # We have them here so that the sanity tests pass without ignores, which
            # reduces the likelihood of further bugs added.
            copy=dict(type='bool', default=True),
            decrypt=dict(type='bool', default=True),
        ),
        add_file_common_args=True,
        # check-mode only works for zip files, we cover that later
        supports_check_mode=True,
        mutually_exclusive=[('include', 'exclude')],
    )

    src = module.params['src']
    dest = module.params['dest']
    abs_dest = os.path.abspath(dest)
    b_dest = to_bytes(abs_dest, errors='surrogate_or_strict')

    if not os.path.isabs(dest):
        module.warn("Relative destination path '{dest}' was resolved to absolute path '{abs_dest}'.".format(dest=dest, abs_dest=abs_dest))

    remote_src = module.params['remote_src']
    file_args = module.load_file_common_arguments(module.params)

    # did tar file arrive?
    if not os.path.exists(src):
        if not remote_src:
            module.fail_json(msg="Source '%s' failed to transfer" % src)
        # If remote_src=true, and src= contains ://, try and download the file to a temp directory.
        elif '://' in src:
            src = fetch_file(module, src)
        else:
            module.fail_json(msg="Source '%s' does not exist" % src)
    if not os.access(src, os.R_OK):
        module.fail_json(msg="Source '%s' not readable" % src)

    # ensure src is an absolute path before picking handlers
    src = os.path.abspath(src)

    # skip working with 0 size archives
    try:
        if os.path.getsize(src) == 0:
            module.fail_json(msg="Invalid archive '%s', the file is 0 bytes" % src)
    except Exception as e:
        module.fail_json(msg="Source '%s' not readable, %s" % (src, to_native(e)))

    # is dest OK to receive tar file?
    if not os.path.isdir(b_dest):
        module.fail_json(msg="Destination '%s' is not a directory" % dest)

    handler = pick_handler(src, b_dest, file_args, module)

    res_args = dict(handler=handler.__class__.__name__, dest=dest, src=src)

    # do we need to do unpack?
    check_results = handler.is_unarchived()

    # DEBUG
    # res_args['check_results'] = check_results

    if module.check_mode:
        res_args['changed'] = not check_results['unarchived']
    elif check_results['unarchived']:
        res_args['changed'] = False
    else:
        # do the unpack
        try:
            res_args['extract_results'] = handler.unarchive()
            if res_args['extract_results']['rc'] != 0:
                module.fail_json(msg="failed to unpack %s to %s" % (src, dest), **res_args)
        except OSError as ex:
            module.fail_json(f"Failed to unpack {src!r} to {dest!r}.", exception=ex, **res_args)
        else:
            res_args['changed'] = True

    # Get diff if required
    if check_results.get('diff', False):
        res_args['diff'] = {'prepared': check_results['diff']}

    # Run only if we found differences (idempotence) or diff was missing
    if res_args.get('diff', True) and not module.check_mode:
        # do we need to change perms?
        top_folders = []
        for filename in handler.files_in_archive:
            file_args['path'] = os.path.join(b_dest, to_bytes(filename, errors='surrogate_or_strict'))

            try:
                res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'], expand=False)
            except OSError as ex:
                module.fail_json("Unexpected error when accessing exploded file.", exception=ex, **res_args)

            if '/' in filename:
                top_folder_path = filename.split('/')[0]
                if top_folder_path not in top_folders:
                    top_folders.append(top_folder_path)

        # make sure top folders have the right permissions
        # https://github.com/ansible/ansible/issues/35426
        if top_folders:
            for f in top_folders:
                file_args['path'] = "%s/%s" % (dest, f)
                try:
                    res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'], expand=False)
                except OSError as ex:
                    module.fail_json("Unexpected error when accessing exploded file.", exception=ex, **res_args)

    if module.params['list_files']:
        res_args['files'] = handler.files_in_archive

    module.exit_json(**res_args)
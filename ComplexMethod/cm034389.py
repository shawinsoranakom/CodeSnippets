def ensure_directory(path, follow, recurse, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])

    # For followed symlinks, we need to operate on the target of the link
    if follow and prev_state == 'link':
        b_path = os.path.realpath(b_path)
        path = to_native(b_path, errors='strict')
        file_args['path'] = path
        prev_state = get_state(b_path)

    changed = False
    diff = initial_diff(path, 'directory', prev_state)

    if prev_state == 'absent':
        # Create directory and assign permissions to it
        if module.check_mode:
            return {'path': path, 'changed': True, 'diff': diff}
        curpath = ''

        try:
            # Split the path so we can apply filesystem attributes recursively
            # from the root (/) directory for absolute paths or the base path
            # of a relative path.  We can then walk the appropriate directory
            # path to apply attributes.
            # Something like mkdir -p with mode applied to all of the newly created directories
            for dirname in path.strip('/').split('/'):
                curpath = '/'.join([curpath, dirname])
                # Remove leading slash if we're creating a relative path
                if not os.path.isabs(path):
                    curpath = curpath.lstrip('/')
                b_curpath = to_bytes(curpath, errors='surrogate_or_strict')
                if not os.path.exists(b_curpath):
                    try:
                        os.mkdir(b_curpath)
                        changed = True
                    except OSError as ex:
                        # Possibly something else created the dir since the os.path.exists
                        # check above. As long as it's a dir, we don't need to error out.
                        if not (ex.errno == errno.EEXIST and os.path.isdir(b_curpath)):
                            raise
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path'] = curpath
                    changed = module.set_fs_attributes_if_different(tmp_file_args, changed, diff, expand=False)
                    changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)
        except Exception as e:
            module.fail_json(
                msg=f"There was an issue creating {curpath} as requested: {to_native(e)}",
                path=path
            )
        return {'path': path, 'changed': changed, 'diff': diff}

    elif prev_state != 'directory':
        # We already know prev_state is not 'absent', therefore it exists in some form.
        module.fail_json(
            msg=f"{path} already exists as a {prev_state}",
            path=path
        )

    #
    # previous state == directory
    #

    changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
    changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)
    if recurse:
        changed |= recursive_set_attributes(b_path, follow, file_args, mtime, atime)

    return {'path': path, 'changed': changed, 'diff': diff}
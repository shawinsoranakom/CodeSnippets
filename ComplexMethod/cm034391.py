def ensure_hardlink(path, src, follow, force, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    b_src = to_bytes(src, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])

    # src is the source of a hardlink.  We require it if we are creating a new hardlink.
    # We require path in the argument_spec so we know it is present at this point.
    if prev_state != 'hard' and src is None:
        module.fail_json(
            msg='src is required for creating new hardlinks'
        )

    # Even if the link already exists, if src was specified it needs to exist.
    # The inode number will be compared to ensure the link has the correct target.
    if src is not None and not os.path.exists(b_src):
        module.fail_json(
            msg='src does not exist',
            dest=path,
            src=src
        )

    diff = initial_diff(path, 'hard', prev_state)
    changed = False

    if prev_state == 'absent':
        changed = True
    elif prev_state == 'link':
        b_old_src = os.readlink(b_path)
        if b_old_src != b_src:
            diff['before']['src'] = to_native(b_old_src, errors='strict')
            diff['after']['src'] = src
            changed = True
    elif prev_state == 'hard':
        if src is not None and os.stat(b_path).st_ino != os.stat(b_src).st_ino:
            changed = True
            if not force:
                module.fail_json(
                    msg='Cannot link, different hard link exists at destination',
                    dest=path,
                    src=src
                )
    elif prev_state == 'file':
        changed = True
        if not force:
            module.fail_json(
                msg=f'Cannot link, {prev_state} exists at destination',
                dest=path,
                src=src
            )
    elif prev_state == 'directory':
        changed = True
        if os.path.exists(b_path):
            if os.stat(b_path).st_ino == os.stat(b_src).st_ino:
                return {'path': path, 'changed': False}
            elif not force:
                module.fail_json(
                    msg='Cannot link: different hard link exists at destination',
                    dest=path,
                    src=src
                )
    else:
        module.fail_json(
            msg='unexpected position reached',
            dest=path,
            src=src
        )

    if changed and not module.check_mode:
        if prev_state != 'absent':
            # try to replace atomically
            b_tmppath = to_bytes(os.path.sep).join(
                [os.path.dirname(b_path), to_bytes(".%s.%s.tmp" % (os.getpid(), time.time()))]
            )
            try:
                if prev_state == 'directory':
                    if os.path.exists(b_path):
                        try:
                            os.unlink(b_path)
                        except FileNotFoundError:
                            pass
                os.link(b_src, b_tmppath)
                os.rename(b_tmppath, b_path)
            except OSError as e:
                if os.path.exists(b_tmppath):
                    os.unlink(b_tmppath)
                module.fail_json(
                    msg=f"Error while replacing: {to_native(e, nonstring='simplerepr')}",
                    path=path
                )
        else:
            try:
                if follow and os.path.islink(b_src):
                    b_src = os.readlink(b_src)
                os.link(b_src, b_path)
            except OSError as e:
                module.fail_json(
                    msg=f"Error while linking: {to_native(e, nonstring='simplerepr')}",
                    path=path
                )

    if module.check_mode and not os.path.exists(b_path):
        return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}

    changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
    changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)

    return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}
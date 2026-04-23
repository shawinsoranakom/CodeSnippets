def ensure_symlink(path, src, follow, force, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    b_src = to_bytes(src, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])
    # source is both the source of a symlink or an informational passing of the src for a template module
    # or copy module, even if this module never uses it, it is needed to key off some things
    if src is None:
        if follow and os.path.exists(b_path):
            # use the current target of the link as the source
            src = to_native(os.readlink(b_path), errors='strict')
            b_src = to_bytes(src, errors='surrogate_or_strict')

    if not os.path.islink(b_path) and os.path.isdir(b_path):
        relpath = path
    else:
        b_relpath = os.path.dirname(b_path)
        relpath = to_native(b_relpath, errors='strict')

    # If src is None that means we are expecting to update an existing link.
    if src is None:
        absrc = None
    else:
        absrc = os.path.join(relpath, src)

    b_absrc = to_bytes(absrc, errors='surrogate_or_strict')
    if not force and src is not None and not os.path.exists(b_absrc):
        module.fail_json(
            msg="src file does not exist, use 'force=yes' if you"
                f" really want to create the link: {absrc}",
            path=path,
            src=src
        )

    if prev_state == 'directory':
        if not force:
            module.fail_json(
                msg=f'refusing to convert from {prev_state} to symlink for {path}',
                path=path
            )
        elif os.listdir(b_path):
            # refuse to replace a directory that has files in it
            module.fail_json(
                msg=f'the directory {path} is not empty, refusing to convert it',
                path=path
            )
    elif prev_state in ('file', 'hard') and not force:
        module.fail_json(
            msg=f'refusing to convert from {prev_state} to symlink for {path}',
            path=path
        )

    diff = initial_diff(path, 'link', prev_state)
    changed = False

    if prev_state in ('hard', 'file', 'directory', 'absent'):
        if src is None:
            module.fail_json(
                msg='src is required for creating new symlinks',
            )
        changed = True
    elif prev_state == 'link':
        if src is not None:
            b_old_src = os.readlink(b_path)
            if b_old_src != b_src:
                diff['before']['src'] = to_native(b_old_src, errors='strict')
                diff['after']['src'] = src
                changed = True
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
                    os.rmdir(b_path)
                os.symlink(b_src, b_tmppath)
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
                os.symlink(b_src, b_path)
            except OSError as e:
                module.fail_json(
                    msg=f"Error while linking: {to_native(e, nonstring='simplerepr')}",
                    path=path
                )

    if module.check_mode and not os.path.exists(b_path):
        return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}

    # Now that we might have created the symlink, get the arguments.
    # We need to do it now so we can properly follow the symlink if needed
    # because load_file_common_arguments sets 'path' according
    # the value of follow and the symlink existence.
    file_args = module.load_file_common_arguments(module.params)

    # Whenever we create a link to a nonexistent target we know that the nonexistent target
    # cannot have any permissions set on it.  Skip setting those and emit a warning (the user
    # can set follow=False to remove the warning)
    if follow and os.path.islink(b_path) and not os.path.exists(file_args['path']):
        module.warn('Cannot set fs attributes on a non-existent symlink target. follow should be'
                    ' set to False to avoid this.')
    else:
        changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
        changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)

    return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}
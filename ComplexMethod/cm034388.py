def update_timestamp_for_file(path, mtime, atime, diff=None):
    b_path = to_bytes(path, errors='surrogate_or_strict')

    try:
        # When mtime and atime are set to 'now', rely on utime(path, None) which does not require ownership of the file
        # https://github.com/ansible/ansible/issues/50943
        if mtime is Sentinel and atime is Sentinel:
            # It's not exact but we can't rely on os.stat(path).st_mtime after setting os.utime(path, None) as it may
            # not be updated. Just use the current time for the diff values
            mtime = atime = time.time()

            previous_mtime = os.stat(b_path).st_mtime
            previous_atime = os.stat(b_path).st_atime

            set_time = None
        else:
            # If both parameters are None 'preserve', nothing to do
            if mtime is None and atime is None:
                return False

            previous_mtime = os.stat(b_path).st_mtime
            previous_atime = os.stat(b_path).st_atime

            if mtime is None:
                mtime = previous_mtime
            elif mtime is Sentinel:
                mtime = time.time()

            if atime is None:
                atime = previous_atime
            elif atime is Sentinel:
                atime = time.time()

            # If both timestamps are already ok, nothing to do
            if mtime == previous_mtime and atime == previous_atime:
                return False

            set_time = (atime, mtime)

        if not module.check_mode:
            os.utime(b_path, set_time)

        if diff is not None:
            if 'before' not in diff:
                diff['before'] = {}
            if 'after' not in diff:
                diff['after'] = {}
            if mtime != previous_mtime:
                diff['before']['mtime'] = previous_mtime
                diff['after']['mtime'] = mtime
            if atime != previous_atime:
                diff['before']['atime'] = previous_atime
                diff['after']['atime'] = atime
    except OSError as e:
        module.fail_json(
            msg=f"Error while updating modification or access time: {to_native(e, nonstring='simplerepr')}",
            path=path
        )
    return True
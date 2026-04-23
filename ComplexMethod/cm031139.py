def _copy_info(info, target, follow_symlinks=True):
    """Copy metadata from the given PathInfo to the given local path."""
    copy_times_ns = (
        hasattr(info, '_access_time_ns') and
        hasattr(info, '_mod_time_ns') and
        (follow_symlinks or os.utime in os.supports_follow_symlinks))
    if copy_times_ns:
        t0 = info._access_time_ns(follow_symlinks=follow_symlinks)
        t1 = info._mod_time_ns(follow_symlinks=follow_symlinks)
        os.utime(target, ns=(t0, t1), follow_symlinks=follow_symlinks)

    # We must copy extended attributes before the file is (potentially)
    # chmod()'ed read-only, otherwise setxattr() will error with -EACCES.
    copy_xattrs = (
        hasattr(info, '_xattrs') and
        hasattr(os, 'setxattr') and
        (follow_symlinks or os.setxattr in os.supports_follow_symlinks))
    if copy_xattrs:
        xattrs = info._xattrs(follow_symlinks=follow_symlinks)
        for attr, value in xattrs:
            try:
                os.setxattr(target, attr, value, follow_symlinks=follow_symlinks)
            except OSError as e:
                if e.errno not in (EPERM, ENOTSUP, ENODATA, EINVAL, EACCES):
                    raise

    copy_posix_permissions = (
        hasattr(info, '_posix_permissions') and
        (follow_symlinks or os.chmod in os.supports_follow_symlinks))
    if copy_posix_permissions:
        posix_permissions = info._posix_permissions(follow_symlinks=follow_symlinks)
        try:
            os.chmod(target, posix_permissions, follow_symlinks=follow_symlinks)
        except NotImplementedError:
            # if we got a NotImplementedError, it's because
            #   * follow_symlinks=False,
            #   * lchown() is unavailable, and
            #   * either
            #       * fchownat() is unavailable or
            #       * fchownat() doesn't implement AT_SYMLINK_NOFOLLOW.
            #         (it returned ENOSUP.)
            # therefore we're out of options--we simply cannot chown the
            # symlink.  give up, suppress the error.
            # (which is what shutil always did in this circumstance.)
            pass

    copy_bsd_flags = (
        hasattr(info, '_bsd_flags') and
        hasattr(os, 'chflags') and
        (follow_symlinks or os.chflags in os.supports_follow_symlinks))
    if copy_bsd_flags:
        bsd_flags = info._bsd_flags(follow_symlinks=follow_symlinks)
        try:
            os.chflags(target, bsd_flags, follow_symlinks=follow_symlinks)
        except OSError as why:
            if why.errno not in (EOPNOTSUPP, ENOTSUP):
                raise
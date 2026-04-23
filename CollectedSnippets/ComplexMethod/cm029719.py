def _make_tarball(base_name, base_dir, compress="gzip", verbose=0, dry_run=0,
                  owner=None, group=None, logger=None, root_dir=None):
    """Create a (possibly compressed) tar file from all the files under
    'base_dir'.

    'compress' must be "gzip" (the default), "bzip2", "xz", "zst", or None.

    'owner' and 'group' can be used to define an owner and a group for the
    archive that is being built. If not provided, the current owner and group
    will be used.

    The output tar file will be named 'base_name' +  ".tar", possibly plus
    the appropriate compression extension (".gz", ".bz2", ".xz", or ".zst").

    Returns the output filename.
    """
    if compress is None:
        tar_compression = ''
    elif _ZLIB_SUPPORTED and compress == 'gzip':
        tar_compression = 'gz'
    elif _BZ2_SUPPORTED and compress == 'bzip2':
        tar_compression = 'bz2'
    elif _LZMA_SUPPORTED and compress == 'xz':
        tar_compression = 'xz'
    elif _ZSTD_SUPPORTED and compress == 'zst':
        tar_compression = 'zst'
    else:
        raise ValueError("bad value for 'compress', or compression format not "
                         "supported : {0}".format(compress))

    import tarfile  # late import for breaking circular dependency

    compress_ext = '.' + tar_compression if compress else ''
    archive_name = base_name + '.tar' + compress_ext
    archive_dir = os.path.dirname(archive_name)

    if archive_dir and not os.path.exists(archive_dir):
        if logger is not None:
            logger.info("creating %s", archive_dir)
        if not dry_run:
            os.makedirs(archive_dir)

    # creating the tarball
    if logger is not None:
        logger.info('Creating tar archive')

    uid = _get_uid(owner)
    gid = _get_gid(group)

    def _set_uid_gid(tarinfo):
        if gid is not None:
            tarinfo.gid = gid
            tarinfo.gname = group
        if uid is not None:
            tarinfo.uid = uid
            tarinfo.uname = owner
        return tarinfo

    if not dry_run:
        tar = tarfile.open(archive_name, 'w|%s' % tar_compression)
        arcname = base_dir
        if root_dir is not None:
            base_dir = os.path.join(root_dir, base_dir)
        try:
            tar.add(base_dir, arcname, filter=_set_uid_gid)
        finally:
            tar.close()

    if root_dir is not None:
        archive_name = os.path.abspath(archive_name)
    return archive_name
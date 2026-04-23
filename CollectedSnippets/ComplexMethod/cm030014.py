def _get_filtered_attrs(member, dest_path, for_data=True):
    new_attrs = {}
    name = member.name
    dest_path = os.path.realpath(dest_path, strict=os.path.ALLOW_MISSING)
    # Strip leading / (tar's directory separator) from filenames.
    # Include os.sep (target OS directory separator) as well.
    if name.startswith(('/', os.sep)):
        name = new_attrs['name'] = member.path.lstrip('/' + os.sep)
    if os.path.isabs(name):
        # Path is absolute even after stripping.
        # For example, 'C:/foo' on Windows.
        raise AbsolutePathError(member)
    # Ensure we stay in the destination
    target_path = os.path.realpath(os.path.join(dest_path, name),
                                   strict=os.path.ALLOW_MISSING)
    if os.path.commonpath([target_path, dest_path]) != dest_path:
        raise OutsideDestinationError(member, target_path)
    # Limit permissions (no high bits, and go-w)
    mode = member.mode
    if mode is not None:
        # Strip high bits & group/other write bits
        mode = mode & 0o755
        if for_data:
            # For data, handle permissions & file types
            if member.isreg() or member.islnk():
                if not mode & 0o100:
                    # Clear executable bits if not executable by user
                    mode &= ~0o111
                # Ensure owner can read & write
                mode |= 0o600
            elif member.isdir() or member.issym():
                # Ignore mode for directories & symlinks
                mode = None
            else:
                # Reject special files
                raise SpecialFileError(member)
        if mode != member.mode:
            new_attrs['mode'] = mode
    if for_data:
        # Ignore ownership for 'data'
        if member.uid is not None:
            new_attrs['uid'] = None
        if member.gid is not None:
            new_attrs['gid'] = None
        if member.uname is not None:
            new_attrs['uname'] = None
        if member.gname is not None:
            new_attrs['gname'] = None
        # Check link destination for 'data'
        if member.islnk() or member.issym():
            if os.path.isabs(member.linkname):
                raise AbsoluteLinkError(member)
            normalized = os.path.normpath(member.linkname)
            if normalized != member.linkname:
                new_attrs['linkname'] = normalized
            if member.issym():
                target_path = os.path.join(dest_path,
                                           os.path.dirname(name),
                                           member.linkname)
            else:
                target_path = os.path.join(dest_path,
                                           member.linkname)
            target_path = os.path.realpath(target_path,
                                           strict=os.path.ALLOW_MISSING)
            if os.path.commonpath([target_path, dest_path]) != dest_path:
                raise LinkOutsideDestinationError(member, target_path)
    return new_attrs
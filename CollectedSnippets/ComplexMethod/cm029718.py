def move(src, dst, copy_function=copy2):
    """Recursively move a file or directory to another location. This is
    similar to the Unix "mv" command. Return the file or directory's
    destination.

    If dst is an existing directory or a symlink to a directory, then src is
    moved inside that directory. The destination path in that directory must
    not already exist.

    If dst already exists but is not a directory, it may be overwritten
    depending on os.rename() semantics.

    If the destination is on our current filesystem, then rename() is used.
    Otherwise, src is copied to the destination and then removed. Symlinks are
    recreated under the new name if os.rename() fails because of cross
    filesystem renames.

    The optional `copy_function` argument is a callable that will be used
    to copy the source or it will be delegated to `copytree`.
    By default, copy2() is used, but any function that supports the same
    signature (like copy()) can be used.

    A lot more could be done here...  A look at a mv.c shows a lot of
    the issues this implementation glosses over.

    """
    sys.audit("shutil.move", src, dst)
    real_dst = dst
    if os.path.isdir(dst):
        if _samefile(src, dst) and not os.path.islink(src):
            # We might be on a case insensitive filesystem,
            # perform the rename anyway.
            os.rename(src, dst)
            return

        # Using _basename instead of os.path.basename is important, as we must
        # ignore any trailing slash to avoid the basename returning ''
        real_dst = os.path.join(dst, _basename(src))

        if os.path.exists(real_dst):
            raise Error("Destination path '%s' already exists" % real_dst)
    try:
        os.rename(src, real_dst)
    except OSError:
        if os.path.islink(src):
            linkto = os.readlink(src)
            os.symlink(linkto, real_dst)
            os.unlink(src)
        elif os.path.isdir(src):
            if _destinsrc(src, dst):
                raise Error("Cannot move a directory '%s' into itself"
                            " '%s'." % (src, dst))
            if (_is_immutable(src)
                    or (not os.access(src, os.W_OK) and os.listdir(src)
                        and sys.platform == 'darwin')):
                raise PermissionError("Cannot move the non-empty directory "
                                      "'%s': Lacking write permission to '%s'."
                                      % (src, src))
            copytree(src, real_dst, copy_function=copy_function,
                     symlinks=True)
            rmtree(src)
        else:
            copy_function(src, real_dst)
            os.unlink(src)
    return real_dst
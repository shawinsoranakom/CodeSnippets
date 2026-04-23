def _walk_dirs(topdir, base_path=None, local_follow=False, trailing_slash_detector=None):
    """
    Walk a filesystem tree returning enough information to copy the files

    :arg topdir: The directory that the filesystem tree is rooted at
    :kwarg base_path: The initial directory structure to strip off of the
        files for the destination directory.  If this is None (the default),
        the base_path is set to ``top_dir``.
    :kwarg local_follow: Whether to follow symlinks on the source.  When set
        to False, no symlinks are dereferenced.  When set to True (the
        default), the code will dereference most symlinks.  However, symlinks
        can still be present if needed to break a circular link.
    :kwarg trailing_slash_detector: Function to determine if a path has
        a trailing directory separator. Only needed when dealing with paths on
        a remote machine (in which case, pass in a function that is aware of the
        directory separator conventions on the remote machine).
    :returns: dictionary of tuples.  All of the path elements in the structure are text strings.
            This separates all the files, directories, and symlinks along with
            important information about each::

                { 'files': [('/absolute/path/to/copy/from', 'relative/path/to/copy/to'), ...],
                  'directories': [('/absolute/path/to/copy/from', 'relative/path/to/copy/to'), ...],
                  'symlinks': [('/symlink/target/path', 'relative/path/to/copy/to'), ...],
                }

        The ``symlinks`` field is only populated if ``local_follow`` is set to False
        *or* a circular symlink cannot be dereferenced.

    """
    # Convert the path segments into byte strings

    r_files = {'files': [], 'directories': [], 'symlinks': []}

    def _recurse(topdir, rel_offset, parent_dirs, rel_base=u''):
        """
        This is a closure (function utilizing variables from it's parent
        function's scope) so that we only need one copy of all the containers.
        Note that this function uses side effects (See the Variables used from
        outer scope).

        :arg topdir: The directory we are walking for files
        :arg rel_offset: Integer defining how many characters to strip off of
            the beginning of a path
        :arg parent_dirs: Directories that we're copying that this directory is in.
        :kwarg rel_base: String to prepend to the path after ``rel_offset`` is
            applied to form the relative path.

        Variables used from the outer scope
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        :r_files: Dictionary of files in the hierarchy.  See the return value
            for :func:`walk` for the structure of this dictionary.
        :local_follow: Read-only inside of :func:`_recurse`. Whether to follow symlinks
        """
        for base_path, sub_folders, files in os.walk(topdir):
            for filename in files:
                filepath = os.path.join(base_path, filename)
                dest_filepath = os.path.join(rel_base, filepath[rel_offset:])

                if os.path.islink(filepath):
                    # Dereference the symlnk
                    real_file = os.path.realpath(filepath)
                    if local_follow and os.path.isfile(real_file):
                        # Add the file pointed to by the symlink
                        r_files['files'].append((real_file, dest_filepath))
                    else:
                        # Mark this file as a symlink to copy
                        r_files['symlinks'].append((os.readlink(filepath), dest_filepath))
                else:
                    # Just a normal file
                    r_files['files'].append((filepath, dest_filepath))

            for dirname in sub_folders:
                dirpath = os.path.join(base_path, dirname)
                dest_dirpath = os.path.join(rel_base, dirpath[rel_offset:])
                real_dir = os.path.realpath(dirpath)
                dir_stats = os.stat(real_dir)

                if os.path.islink(dirpath):
                    if local_follow:
                        if (dir_stats.st_dev, dir_stats.st_ino) in parent_dirs:
                            # Just insert the symlink if the target directory
                            # exists inside of the copy already
                            r_files['symlinks'].append((os.readlink(dirpath), dest_dirpath))
                        else:
                            # Walk the dirpath to find all parent directories.
                            new_parents = set()
                            parent_dir_list = os.path.dirname(dirpath).split(os.path.sep)
                            for parent in range(len(parent_dir_list), 0, -1):
                                parent_stat = os.stat(u'/'.join(parent_dir_list[:parent]))
                                if (parent_stat.st_dev, parent_stat.st_ino) in parent_dirs:
                                    # Reached the point at which the directory
                                    # tree is already known.  Don't add any
                                    # more or we might go to an ancestor that
                                    # isn't being copied.
                                    break
                                new_parents.add((parent_stat.st_dev, parent_stat.st_ino))

                            if (dir_stats.st_dev, dir_stats.st_ino) in new_parents:
                                # This was a circular symlink.  So add it as
                                # a symlink
                                r_files['symlinks'].append((os.readlink(dirpath), dest_dirpath))
                            else:
                                # Walk the directory pointed to by the symlink
                                r_files['directories'].append((real_dir, dest_dirpath))
                                offset = len(real_dir) + 1
                                _recurse(real_dir, offset, parent_dirs.union(new_parents), rel_base=dest_dirpath)
                    else:
                        # Add the symlink to the destination
                        r_files['symlinks'].append((os.readlink(dirpath), dest_dirpath))
                else:
                    # Just a normal directory
                    r_files['directories'].append((dirpath, dest_dirpath))

    # Check if the source ends with a "/" so that we know which directory
    # level to work at (similar to rsync)
    source_trailing_slash = False
    if trailing_slash_detector:
        source_trailing_slash = trailing_slash_detector(topdir)
    else:
        source_trailing_slash = topdir.endswith(os.path.sep)

    # Calculate the offset needed to strip the base_path to make relative
    # paths
    if base_path is None:
        base_path = topdir
    if not source_trailing_slash:
        base_path = os.path.dirname(base_path)
    if topdir.startswith(base_path):
        offset = len(base_path)

    # Make sure we're making the new paths relative
    if trailing_slash_detector and not trailing_slash_detector(base_path):
        offset += 1
    elif not base_path.endswith(os.path.sep):
        offset += 1

    if os.path.islink(topdir) and not local_follow:
        r_files['symlinks'] = (os.readlink(topdir), os.path.basename(topdir))
        return r_files

    dir_stats = os.stat(topdir)
    parents = frozenset(((dir_stats.st_dev, dir_stats.st_ino),))
    # Actually walk the directory hierarchy
    _recurse(topdir, offset, parents)

    return r_files
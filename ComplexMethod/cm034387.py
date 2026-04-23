def recursive_set_attributes(b_path, follow, file_args, mtime, atime):
    changed = False

    try:
        for b_root, b_dirs, b_files in os.walk(b_path):
            for b_fsobj in b_dirs + b_files:
                b_fsname = os.path.join(b_root, b_fsobj)
                if not os.path.islink(b_fsname):
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                    changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
                    changed |= update_timestamp_for_file(tmp_file_args['path'], mtime, atime)

                else:
                    # Change perms on the link
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                    changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
                    changed |= update_timestamp_for_file(tmp_file_args['path'], mtime, atime)

                    if follow:
                        b_fsname = os.path.join(b_root, os.readlink(b_fsname))
                        # The link target could be nonexistent
                        if os.path.exists(b_fsname):
                            if os.path.isdir(b_fsname):
                                # Link is a directory so change perms on the directory's contents
                                changed |= recursive_set_attributes(b_fsname, follow, file_args, mtime, atime)

                            # Change perms on the file pointed to by the link
                            tmp_file_args = file_args.copy()
                            tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                            changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
                            changed |= update_timestamp_for_file(tmp_file_args['path'], mtime, atime)
    except RuntimeError as e:
        # on Python3 "RecursionError" is raised which is derived from "RuntimeError"
        # TODO once this function is moved into the common file utilities, this should probably raise more general exception
        module.fail_json(
            msg=f"Could not recursively set attributes on {to_native(b_path)}. Original error was: '{to_native(e)}'"
        )

    return changed
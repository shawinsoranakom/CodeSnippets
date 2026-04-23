def _walk(b_path, b_top_level_dir):
        b_rel_base_dir = _discover_relative_base_directory(b_path, b_top_level_dir)
        for b_item in os.listdir(b_path):
            b_abs_path = os.path.join(b_path, b_item)
            b_rel_path = os.path.join(b_rel_base_dir, b_item)
            rel_path = to_text(b_rel_path, errors='surrogate_or_strict')

            if os.path.isdir(b_abs_path):
                if any(b_item == b_path for b_path in b_ignore_dirs) or \
                        any(fnmatch.fnmatch(b_rel_path, b_pattern) for b_pattern in b_ignore_patterns):
                    display.vvv("Skipping '%s' for collection build" % to_text(b_abs_path))
                    continue

                if os.path.islink(b_abs_path):
                    b_link_target = os.path.realpath(b_abs_path)

                    if not _is_child_path(b_link_target, b_top_level_dir):
                        display.warning("Skipping '%s' as it is a symbolic link to a directory outside the collection"
                                        % to_text(b_abs_path))
                        continue

                manifest['files'].append(_make_entry(rel_path, 'dir'))

                if not os.path.islink(b_abs_path):
                    _walk(b_abs_path, b_top_level_dir)
            else:
                if any(fnmatch.fnmatch(b_rel_path, b_pattern) for b_pattern in b_ignore_patterns):
                    display.vvv("Skipping '%s' for collection build" % to_text(b_abs_path))
                    continue

                # Handling of file symlinks occur in _build_collection_tar, the manifest for a symlink is the same for
                # a normal file.
                manifest['files'].append(
                    _make_entry(
                        rel_path,
                        'file',
                        chksum_type='sha256',
                        chksum=secure_hash(b_abs_path, hash_func=sha256)
                    )
                )
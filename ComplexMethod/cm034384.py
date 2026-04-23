def copy_left_only(src, dest, module):
    """Copy files that exist in `src` directory only to the `dest` directory."""

    changed = False
    owner = module.params['owner']
    group = module.params['group']
    local_follow = module.params['local_follow']
    left_only = filecmp.dircmp(src, dest).left_only
    if len(left_only):
        changed = True
    if not module.check_mode:
        for item in left_only:
            src_item_path = os.path.join(src, item)
            dest_item_path = os.path.join(dest, item)
            b_src_item_path = to_bytes(src_item_path, errors='surrogate_or_strict')
            b_dest_item_path = to_bytes(dest_item_path, errors='surrogate_or_strict')

            if os.path.islink(b_src_item_path) and os.path.isdir(b_src_item_path) and local_follow is True:
                shutil.copytree(b_src_item_path, b_dest_item_path, symlinks=not local_follow)
                chown_recursive(b_dest_item_path, module)

            if os.path.islink(b_src_item_path) and os.path.isdir(b_src_item_path) and local_follow is False:
                linkto = os.readlink(b_src_item_path)
                os.symlink(linkto, b_dest_item_path)

            if os.path.islink(b_src_item_path) and os.path.isfile(b_src_item_path) and local_follow is True:
                shutil.copyfile(b_src_item_path, b_dest_item_path)
                chown_path(module, b_dest_item_path, owner, group)

            if os.path.islink(b_src_item_path) and os.path.isfile(b_src_item_path) and local_follow is False:
                linkto = os.readlink(b_src_item_path)
                os.symlink(linkto, b_dest_item_path)

            if not os.path.islink(b_src_item_path) and os.path.isfile(b_src_item_path):
                shutil.copyfile(b_src_item_path, b_dest_item_path)
                shutil.copymode(b_src_item_path, b_dest_item_path)
                chown_path(module, b_dest_item_path, owner, group)

            if not os.path.islink(b_src_item_path) and os.path.isdir(b_src_item_path):
                shutil.copytree(b_src_item_path, b_dest_item_path, symlinks=not local_follow)
                chown_recursive(b_dest_item_path, module)

            changed = True
    return changed
def _build_collection_dir(b_collection_path, b_collection_output, collection_manifest, file_manifest):
    """Build a collection directory from the manifest data.

    This should follow the same pattern as _build_collection_tar.
    """
    os.makedirs(b_collection_output, mode=S_IRWXU_RXG_RXO)

    files_manifest_json = to_bytes(json.dumps(file_manifest, indent=True, sort_keys=True), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest, indent=True), errors='surrogate_or_strict')

    # Write contents to the files
    for name, b in [(MANIFEST_FILENAME, collection_manifest_json), ('FILES.json', files_manifest_json)]:
        b_path = os.path.join(b_collection_output, to_bytes(name, errors='surrogate_or_strict'))
        with open(b_path, 'wb') as file_obj, BytesIO(b) as b_io:
            shutil.copyfileobj(b_io, file_obj)

        os.chmod(b_path, S_IRWU_RG_RO)

    base_directories = []
    for file_info in file_manifest['files']:
        if file_info['name'] == '.':
            continue

        src_file = os.path.join(b_collection_path, to_bytes(file_info['name'], errors='surrogate_or_strict'))
        dest_file = os.path.join(b_collection_output, to_bytes(file_info['name'], errors='surrogate_or_strict'))

        existing_is_exec = os.stat(src_file, follow_symlinks=False).st_mode & stat.S_IXUSR
        mode = S_IRWXU_RXG_RXO if existing_is_exec else S_IRWU_RG_RO

        # ensure symlinks to dirs are not translated to empty dirs
        if os.path.isdir(src_file) and not os.path.islink(src_file):
            mode = S_IRWXU_RXG_RXO
            base_directories.append(src_file)
            os.mkdir(dest_file, mode)
        else:
            # do not follow symlinks to ensure the original link is used
            shutil.copyfile(src_file, dest_file, follow_symlinks=False)

        # avoid setting specific permission on symlinks since it does not
        # support avoid following symlinks and will thrown an exception if the
        # symlink target does not exist
        if not os.path.islink(dest_file):
            os.chmod(dest_file, mode)

    collection_output = to_text(b_collection_output)
    return collection_output
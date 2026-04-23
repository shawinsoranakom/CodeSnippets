def write_signed_by_key(module, v, slug):
    changed = False
    if os.path.isfile(v):
        return changed, v, None

    b_data = None

    parts = generic_urlparse(urlparse(v))
    if parts.scheme:
        try:
            r = open_url(v, http_agent=get_user_agent())
        except Exception as exc:
            raise RuntimeError('Could not fetch signed_by key.') from exc
        else:
            b_data = r.read()
    else:
        # Not a file, nor a URL, just pass it through
        return changed, None, v

    if not b_data:
        return changed, v, None

    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(tmpfd, 'wb') as f:
        f.write(b_data)

    ext = 'asc' if is_armored(b_data) else 'gpg'
    filename = make_signed_by_filename(slug, ext)

    src_chksum = module.sha256(tmpfile)
    dest_chksum = module.sha256(filename)

    if src_chksum != dest_chksum:
        changed |= ensure_keyrings_dir(module)
        if not module.check_mode:
            module.atomic_move(tmpfile, filename)
        changed |= True

    changed |= module.set_mode_if_different(filename, S_IRWU_RG_RO, False)

    return changed, filename, None
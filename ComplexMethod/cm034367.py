def write_file(module, dest, content, resp):
    """
    Create temp file and write content to dest file only if content changed
    """

    tmpsrc = None

    try:
        fd, tmpsrc = tempfile.mkstemp(dir=module.tmpdir)
        with os.fdopen(fd, 'wb') as f:
            if isinstance(content, bytes):
                f.write(content)
            else:
                shutil.copyfileobj(content, f)
    except Exception as e:
        if tmpsrc and os.path.exists(tmpsrc):
            os.remove(tmpsrc)
        msg = format_message("Failed to create temporary content file: %s" % to_native(e), resp)
        module.fail_json(msg=msg, **resp)

    checksum_src = module.sha1(tmpsrc)
    checksum_dest = module.sha1(dest)

    if checksum_src != checksum_dest:
        try:
            module.atomic_move(tmpsrc, dest)
        except Exception as e:
            if os.path.exists(tmpsrc):
                os.remove(tmpsrc)
            msg = format_message("failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(e)), resp)
            module.fail_json(msg=msg, **resp)

    if os.path.exists(tmpsrc):
        os.remove(tmpsrc)
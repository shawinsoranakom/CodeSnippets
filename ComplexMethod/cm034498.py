def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest', 'name']),
            follow=dict(type='bool', default=False),
            get_checksum=dict(type='bool', default=True),
            get_mime=dict(type='bool', default=True, aliases=['mime', 'mime_type', 'mime-type']),
            get_attributes=dict(type='bool', default=True, aliases=['attr', 'attributes']),
            get_selinux_context=dict(type='bool', default=False),
            checksum_algorithm=dict(type='str', default='sha1',
                                    choices=['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'],
                                    aliases=['checksum', 'checksum_algo']),
        ),
        supports_check_mode=True,
    )

    path = module.params.get('path')
    b_path = to_bytes(path, errors='surrogate_or_strict')
    follow = module.params.get('follow')
    get_mime = module.params.get('get_mime')
    get_attr = module.params.get('get_attributes')
    get_checksum = module.params.get('get_checksum')
    checksum_algorithm = module.params.get('checksum_algorithm')
    get_selinux_context = module.params.get('get_selinux_context')

    # main stat data
    try:
        if follow:
            st = os.stat(b_path)
        else:
            st = os.lstat(b_path)
    except FileNotFoundError:
        output = {'exists': False}
        module.exit_json(changed=False, stat=output)
    except OSError as ex:
        module.fail_json(msg=ex.strerror, exception=ex)

    # process base results
    output = format_output(module, path, st)

    # resolved permissions
    for perm in [('readable', os.R_OK), ('writeable', os.W_OK), ('executable', os.X_OK)]:
        output[perm[0]] = os.access(b_path, perm[1])

    # symlink info
    if output.get('islnk'):
        output['lnk_source'] = os.path.realpath(b_path)
        output['lnk_target'] = os.readlink(b_path)

    try:  # user data
        pw = pwd.getpwuid(st.st_uid)
        output['pw_name'] = pw.pw_name
    except (TypeError, KeyError):
        pass

    try:  # group data
        grp_info = grp.getgrgid(st.st_gid)
        output['gr_name'] = grp_info.gr_name
    except (KeyError, ValueError, OverflowError):
        pass

    # checksums
    if output.get('isreg') and output.get('readable'):
        if get_checksum:
            output['checksum'] = module.digest_from_file(b_path, checksum_algorithm)

    # try to get mime data if requested
    if get_mime:
        output['mimetype'] = output['charset'] = 'unknown'
        mimecmd = module.get_bin_path('file')
        if mimecmd:
            mimecmd = [mimecmd, '--mime-type', '--mime-encoding', b_path]
            try:
                rc, out, err = module.run_command(mimecmd)
                if rc == 0:
                    mimetype, charset = out.rsplit(':', 1)[1].split(';')
                    output['mimetype'] = mimetype.strip()
                    output['charset'] = charset.split('=')[1].strip()
            except Exception:
                pass

    # try to get attr data
    if get_attr:
        output['version'] = None
        output['attributes'] = []
        output['attr_flags'] = ''
        out = module.get_file_attributes(b_path)
        for x in ('version', 'attributes', 'attr_flags'):
            if x in out:
                output[x] = out[x]

    # try to get SELinux context
    if get_selinux_context:
        output['selinux_context'] = module.selinux_context(b_path)

    module.exit_json(changed=False, stat=output)
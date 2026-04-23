def main():

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            src=dict(type='path', required=True),
            delimiter=dict(type='str'),
            dest=dict(type='path', required=True),
            backup=dict(type='bool', default=False),
            remote_src=dict(type='bool', default=True),
            regexp=dict(type='str'),
            ignore_hidden=dict(type='bool', default=False),
            validate=dict(type='str'),

            # Options that are for the action plugin, but ignored by the module itself.
            # We have them here so that the tests pass without ignores, which
            # reduces the likelihood of further bugs added.
            decrypt=dict(type='bool', default=True),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    changed = False
    path_hash = None
    dest_hash = None
    src = module.params['src']
    dest = module.params['dest']
    backup = module.params['backup']
    delimiter = module.params['delimiter']
    regexp = module.params['regexp']
    compiled_regexp = None
    ignore_hidden = module.params['ignore_hidden']
    validate = module.params.get('validate', None)

    result = dict(src=src, dest=dest)
    if not os.path.exists(src):
        module.fail_json(msg="Source (%s) does not exist" % src)

    if not os.path.isdir(src):
        module.fail_json(msg="Source (%s) is not a directory" % src)

    if regexp is not None:
        try:
            compiled_regexp = re.compile(regexp)
        except re.error as e:
            module.fail_json(msg="Invalid Regexp (%s) in \"%s\"" % (to_native(e), regexp))

    if validate and "%s" not in validate:
        module.fail_json(msg="validate must contain %%s: %s" % validate)

    path = assemble_from_fragments(src, delimiter, compiled_regexp, ignore_hidden, module.tmpdir)
    path_hash = module.sha1(path)
    result['checksum'] = path_hash

    # Backwards compat.  This won't return data if FIPS mode is active
    try:
        pathmd5 = module.md5(path)
    except ValueError:
        pathmd5 = None
    result['md5sum'] = pathmd5

    if os.path.exists(dest):
        dest_hash = module.sha1(dest)

    if path_hash != dest_hash:
        if validate:
            (rc, out, err) = module.run_command(validate % path)
            result['validation'] = dict(rc=rc, stdout=out, stderr=err)
            if rc != 0:
                cleanup(module, path)
                module.fail_json(msg="failed to validate: rc:%s error:%s" % (rc, err))
        if backup and dest_hash is not None:
            result['backup_file'] = module.backup_local(dest)

        if not module.check_mode:
            module.atomic_move(path, dest, unsafe_writes=module.params['unsafe_writes'])
        changed = True

    cleanup(module, path, result)

    # handle file permissions (check mode aware)
    file_args = module.load_file_common_arguments(module.params)
    result['changed'] = module.set_fs_attributes_if_different(file_args, changed)

    # Mission complete
    result['msg'] = "OK"
    module.exit_json(**result)
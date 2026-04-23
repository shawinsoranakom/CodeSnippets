def main():

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            src=dict(type='path'),
            _original_basename=dict(type='str'),  # used to handle 'dest is a directory' via template, a slight hack
            content=dict(type='str', no_log=True),
            dest=dict(type='path', required=True),
            backup=dict(type='bool', default=False),
            force=dict(type='bool', default=True),
            validate=dict(type='str'),
            directory_mode=dict(type='raw'),
            remote_src=dict(type='bool', default=False),
            local_follow=dict(type='bool'),
            checksum=dict(type='str'),
            follow=dict(type='bool', default=False),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    src = module.params['src']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    dest = module.params['dest']
    # Make sure we always have a directory component for later processing
    if os.path.sep not in dest:
        dest = '.{0}{1}'.format(os.path.sep, dest)
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    backup = module.params['backup']
    force = module.params['force']
    _original_basename = module.params.get('_original_basename', None)
    validate = module.params.get('validate', None)
    follow = module.params['follow']
    local_follow = module.params['local_follow']
    mode = module.params['mode']
    owner = module.params['owner']
    group = module.params['group']
    remote_src = module.params['remote_src']
    checksum = module.params['checksum']

    if not os.path.exists(b_src):
        module.fail_json(msg="Source %s not found" % (src))
    if not os.access(b_src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))

    # Preserve is usually handled in the action plugin but mode + remote_src has to be done on the
    # remote host
    if module.params['mode'] == 'preserve':
        module.params['mode'] = '0%03o' % stat.S_IMODE(os.stat(b_src).st_mode)
    mode = module.params['mode']

    changed = False

    checksum_dest = None
    checksum_src = None
    md5sum_src = None

    if os.path.isfile(src):
        try:
            checksum_src = module.sha1(src)
        except OSError as ex:
            module.error_as_warning("Unable to calculate src checksum, assuming change.", exception=ex)
        try:
            # Backwards compat only.  This will be None in FIPS mode
            md5sum_src = module.md5(src)
        except ValueError:
            pass
    elif remote_src and not os.path.isdir(src):
        module.fail_json("Cannot copy invalid source '%s': not a file" % to_native(src))

    if checksum and checksum_src != checksum:
        module.fail_json(
            msg='Copied file does not match the expected checksum. Transfer failed.',
            checksum=checksum_src,
            expected_checksum=checksum
        )

    # Special handling for recursive copy - create intermediate dirs
    if dest.endswith(os.sep):
        if _original_basename:
            dest = os.path.join(dest, _original_basename)
        b_dest = to_bytes(dest, errors='surrogate_or_strict')
        dirname = os.path.dirname(dest)
        b_dirname = to_bytes(dirname, errors='surrogate_or_strict')
        if not os.path.exists(b_dirname):
            try:
                (pre_existing_dir, new_directory_list) = split_pre_existing_dir(dirname)
            except AnsibleModuleError as e:
                e.result['msg'] += ' Could not copy to {0}'.format(dest)
                module.fail_json(**e.results)

            if module.check_mode:
                module.exit_json(msg='dest directory %s would be created' % dirname, changed=True, src=src)
            os.makedirs(b_dirname)
            changed = True
            directory_args = module.load_file_common_arguments(module.params)
            directory_mode = module.params["directory_mode"]
            if directory_mode is not None:
                directory_args['mode'] = directory_mode
            else:
                directory_args['mode'] = None
            adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed)

    if os.path.isdir(b_dest):
        basename = os.path.basename(src)
        if _original_basename:
            basename = _original_basename
        dest = os.path.join(dest, basename)
        b_dest = to_bytes(dest, errors='surrogate_or_strict')

    if os.path.exists(b_dest):
        if os.path.islink(b_dest) and follow:
            b_dest = os.path.realpath(b_dest)
            dest = to_native(b_dest, errors='surrogate_or_strict')
        if not force:
            module.exit_json(msg="file already exists", src=src, dest=dest, changed=False)
        if os.access(b_dest, os.R_OK) and os.path.isfile(b_dest):
            checksum_dest = module.sha1(dest)
    else:
        if not os.path.exists(os.path.dirname(b_dest)):
            try:
                # os.path.exists() can return false in some
                # circumstances where the directory does not have
                # the execute bit for the current user set, in
                # which case the stat() call will raise an OSError
                os.stat(os.path.dirname(b_dest))
            except OSError as e:
                if "permission denied" in to_native(e).lower():
                    module.fail_json(msg="Destination directory %s is not accessible" % (os.path.dirname(dest)))
            module.fail_json(msg="Destination directory %s does not exist" % (os.path.dirname(dest)))

    if not os.access(os.path.dirname(b_dest), os.W_OK) and not module.params['unsafe_writes']:
        module.fail_json(msg="Destination %s not writable" % (os.path.dirname(dest)))

    backup_file = None
    if checksum_src != checksum_dest or os.path.islink(b_dest):

        if not module.check_mode:
            try:
                if backup:
                    if os.path.exists(b_dest):
                        backup_file = module.backup_local(dest)
                # allow for conversion from symlink.
                if os.path.islink(b_dest):
                    os.unlink(b_dest)
                    open(b_dest, 'w').close()
                if validate:
                    # if we have a mode, make sure we set it on the temporary
                    # file source as some validations may require it
                    module.set_mode_if_different(src, mode, False)
                    chown_path(module, src, owner, group)
                    if "%s" not in validate:
                        module.fail_json(msg="validate must contain %%s: %s" % (validate))
                    (rc, out, err) = module.run_command(validate % src)
                    if rc != 0:
                        module.fail_json(msg="failed to validate", exit_status=rc, stdout=out, stderr=err)

                b_mysrc = b_src
                if remote_src and os.path.isfile(b_src):

                    dummy, b_mysrc = tempfile.mkstemp(dir=os.path.dirname(b_dest))

                    shutil.copyfile(b_src, b_mysrc)
                    try:
                        shutil.copystat(b_src, b_mysrc)
                    except OSError as err:
                        if err.errno == errno.ENOSYS and mode == "preserve":
                            module.warn("Unable to copy stats {0}".format(to_native(b_src)))
                        else:
                            raise

                # at this point we should always have tmp file
                module.atomic_move(b_mysrc, dest, unsafe_writes=module.params['unsafe_writes'], keep_dest_attrs=not remote_src)

            except OSError as ex:
                raise Exception(f"Failed to copy {src!r} to {dest!r}.") from ex
        changed = True

    # If neither have checksums, both src and dest are directories.
    checksums_none = checksum_src is None and checksum_dest is None
    both_directories = os.path.isdir(module.params['src']) and (os.path.isdir(module.params['dest']) or not os.path.exists(module.params['dest']))
    if checksums_none and remote_src and both_directories:
        b_src = to_bytes(module.params['src'], errors='surrogate_or_strict')
        b_dest = to_bytes(module.params['dest'], errors='surrogate_or_strict')

        if not b_src.endswith(to_bytes(os.path.sep)):
            b_basename = os.path.basename(b_src)
            b_dest = os.path.join(b_dest, b_basename)
            b_src = os.path.join(b_src, b'')

        changed |= copy_directory(b_src, b_dest, module)

    res_args = dict(
        dest=dest, src=src, md5sum=md5sum_src, checksum=checksum_src, changed=changed
    )
    if backup_file:
        res_args['backup_file'] = backup_file

    file_args = module.load_file_common_arguments(module.params, path=dest)
    directory_mode = module.params['directory_mode']
    if os.path.isdir(b_dest) and directory_mode is not None:
        file_args['mode'] = directory_mode
    res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'])

    module.exit_json(**res_args)
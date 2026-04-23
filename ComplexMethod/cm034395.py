def main():
    ssh_defaults = dict(
        bits=0,
        type='rsa',
        passphrase=None,
        comment='ansible-generated on %s' % socket.gethostname()
    )
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            name=dict(type='str', required=True, aliases=['user']),
            uid=dict(type='int'),
            non_unique=dict(type='bool', default=False),
            group=dict(type='str'),
            groups=dict(type='list', elements='str'),
            comment=dict(type='str'),
            home=dict(type='path'),
            shell=dict(type='path'),
            password=dict(type='str', no_log=True),
            login_class=dict(type='str'),
            password_expire_max=dict(type='int', no_log=False),
            password_expire_min=dict(type='int', no_log=False),
            password_expire_warn=dict(type='int', no_log=False),
            # following options are specific to macOS
            hidden=dict(type='bool'),
            # following options are specific to selinux
            seuser=dict(type='str'),
            # following options are specific to userdel
            force=dict(type='bool', default=False),
            remove=dict(type='bool', default=False),
            # following options are specific to useradd
            create_home=dict(type='bool', default=True, aliases=['createhome']),
            skeleton=dict(type='str'),
            system=dict(type='bool', default=False),
            # following options are specific to usermod
            move_home=dict(type='bool', default=False),
            append=dict(type='bool', default=False),
            # following are specific to ssh key generation
            generate_ssh_key=dict(type='bool'),
            ssh_key_bits=dict(type='int', default=ssh_defaults['bits']),
            ssh_key_type=dict(type='str', default=ssh_defaults['type']),
            ssh_key_file=dict(type='path'),
            ssh_key_comment=dict(type='str', default=ssh_defaults['comment']),
            ssh_key_passphrase=dict(type='str', no_log=True),
            update_password=dict(type='str', default='always', choices=['always', 'on_create'], no_log=False),
            expires=dict(type='float'),
            password_lock=dict(type='bool', no_log=False),
            local=dict(type='bool'),
            profile=dict(type='str'),
            authorization=dict(type='str'),
            role=dict(type='str'),
            umask=dict(type='str'),
            password_expire_account_disable=dict(type='int', no_log=False),
            uid_min=dict(type='int'),
            uid_max=dict(type='int'),
        ),
        supports_check_mode=True,
        required_if=[
            ['append', True, ['groups']],
        ],
    )

    user = User(module)
    user.check_password_encrypted()

    if user.seuser is not None and not module.selinux_enabled():
        module.warn(
            f"'seuser' is set to '{user.seuser}' but SELinux is not enabled on "
            f"this system. The 'seuser' parameter will be ignored."
        )

    module.debug('User instantiated - platform %s' % user.platform)
    if user.distribution:
        module.debug('User instantiated - distribution %s' % user.distribution)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = user.name
    result['state'] = user.state
    if user.state == 'absent':
        if user.user_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = user.remove_user()
            if rc != 0:
                module.fail_json(name=user.name, msg=err, rc=rc)
            result['force'] = user.force
            result['remove'] = user.remove
    elif user.state == 'present':
        if not user.user_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            # Check to see if the provided home path contains parent directories
            # that do not exist.
            path_needs_parents = False
            if user.home and user.create_home:
                parent = os.path.dirname(user.home)
                if not os.path.isdir(parent):
                    path_needs_parents = True

            (rc, out, err) = user.create_user()

            # If the home path had parent directories that needed to be created,
            # make sure file permissions are correct in the created home directory.
            if path_needs_parents:
                info = user.user_info()
                if info is not False:
                    user.chown_homedir(info[2], info[3], user.home)

            if module.check_mode:
                result['system'] = user.name
            else:
                result['system'] = user.system
                result['create_home'] = user.create_home
        else:
            # modify user (note: this function is check mode aware)
            (rc, out, err) = user.modify_user()
            result['append'] = user.append
            result['move_home'] = user.move_home
        if rc is not None and rc != 0:
            module.fail_json(name=user.name, msg=err, rc=rc)
        if user.password is not None:
            result['password'] = 'NOT_LOGGING_PASSWORD'

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    if user.user_exists() and user.state == 'present':
        info = user.user_info()
        if info is False:
            result['msg'] = "failed to look up user name: %s" % user.name
            result['failed'] = True
        result['uid'] = info[2]
        result['group'] = info[3]
        result['comment'] = info[4]
        result['home'] = info[5]
        result['shell'] = info[6]
        result['groups'] = ','.join(user.user_group_membership())

        # handle missing homedirs
        info = user.user_info()
        if user.home is None:
            user.home = info[5]
        if not os.path.exists(user.home) and user.home not in PLACEHOLDER_HOME_DIRS and user.create_home:
            if not module.check_mode:
                user.create_homedir(user.home)
                user.chown_homedir(info[2], info[3], user.home)
            result['changed'] = True

        # deal with ssh key
        if user.sshkeygen:
            # generate ssh key (note: this function is check mode aware)
            (rc, out, err) = user.ssh_key_gen()
            if rc is not None and rc != 0:
                module.fail_json(name=user.name, msg=err, rc=rc)
            if rc == 0:
                result['changed'] = True
            (rc, out, err) = user.ssh_key_fingerprint()
            if rc == 0:
                result['ssh_fingerprint'] = out.strip()
            else:
                result['ssh_fingerprint'] = err.strip()
            result['ssh_key_file'] = user.get_ssh_key_path()
            result['ssh_public_key'] = user.get_ssh_public_key()

        (rc, out, err) = user.set_password_expire()
        if rc is None:
            pass  # target state reached, nothing to do
        else:
            if rc != 0:
                module.fail_json(name=user.name, msg=err, rc=rc)
            else:
                result['changed'] = True

    module.exit_json(**result)
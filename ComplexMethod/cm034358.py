def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            name=dict(type='str', required=True),
            force=dict(type='bool', default=False),
            gid=dict(type='int'),
            system=dict(type='bool', default=False),
            local=dict(type='bool', default=False),
            non_unique=dict(type='bool', default=False),
            gid_min=dict(type='int'),
            gid_max=dict(type='int'),
        ),
        supports_check_mode=True,
        required_if=[
            ['non_unique', True, ['gid']],
        ],
    )

    if module.params['force'] and module.params['local']:
        module.fail_json(msg='force is not a valid option for local, force=True and local=True are mutually exclusive')

    group = Group(module)

    module.debug('Group instantiated - platform %s' % group.platform)
    if group.distribution:
        module.debug('Group instantiated - distribution %s' % group.distribution)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = group.name
    result['state'] = group.state

    if group.state == 'absent':

        if group.group_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = group.group_del()
            if rc != 0:
                module.fail_json(name=group.name, msg=err)

    elif group.state == 'present':

        if not group.group_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = group.group_add(gid=group.gid, system=group.system)
        else:
            (rc, out, err) = group.group_mod(gid=group.gid)

        if rc is not None and rc != 0:
            module.fail_json(name=group.name, msg=err)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    if group.group_exists():
        info = group.group_info()
        result['system'] = group.system
        result['gid'] = info[2]

    module.exit_json(**result)
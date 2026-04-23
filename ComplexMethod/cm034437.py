def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', choices=['started', 'stopped', 'reloaded', 'restarted']),
            sleep=dict(type='int'),
            pattern=dict(type='str'),
            enabled=dict(type='bool'),
            runlevel=dict(type='str', default='default'),
            arguments=dict(type='str', default='', aliases=['args']),
        ),
        supports_check_mode=True,
        required_one_of=[['state', 'enabled']],
    )

    service = Service(module)

    module.debug('Service instantiated - platform %s' % service.platform)
    if service.distribution:
        module.debug('Service instantiated - distribution %s' % service.distribution)

    rc = 0
    out = ''
    err = ''
    result = {}
    result['name'] = service.name

    # Find service management tools
    service.get_service_tools()

    # Enable/disable service startup at boot if requested
    if service.module.params['enabled'] is not None:
        # FIXME: ideally this should detect if we need to toggle the enablement state, though
        # it's unlikely the changed handler would need to fire in this case so it's a minor thing.
        service.service_enable()
        result['enabled'] = service.enable

    if module.params['state'] is None:
        # Not changing the running state, so bail out now.
        result['changed'] = service.changed
        module.exit_json(**result)

    result['state'] = service.state

    # Collect service status
    if service.pattern:
        service.check_ps()
    else:
        service.get_service_status()

    # Calculate if request will change service state
    service.check_service_changed()

    # Modify service state if necessary
    (rc, out, err) = service.modify_service_state()

    if rc != 0:
        if err and "Job is already running" in err:
            # upstart got confused, one such possibility is MySQL on Ubuntu 12.04
            # where status may report it has no start/stop links and we could
            # not get accurate status
            pass
        else:
            if err:
                module.fail_json(msg=err)
            else:
                module.fail_json(msg=out)

    result['changed'] = service.changed | service.svc_change
    if service.module.params['enabled'] is not None:
        result['enabled'] = service.module.params['enabled']

    if not service.module.params['state']:
        status = service.get_service_status()
        if status is None:
            result['state'] = 'absent'
        elif status is False:
            result['state'] = 'started'
        else:
            result['state'] = 'stopped'
    else:
        # as we may have just bounced the service the service command may not
        # report accurate state at this moment so just show what we ran
        if service.module.params['state'] in ['reloaded', 'restarted', 'started']:
            result['state'] = 'started'
        else:
            result['state'] = 'stopped'

    module.exit_json(**result)
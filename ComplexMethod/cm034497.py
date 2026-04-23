def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str', aliases=['service']),
            state=dict(choices=['started', 'stopped', 'restarted', 'reloaded'], type='str'),
            enabled=dict(type='bool'),
            sleep=dict(type='int', default=1),
            pattern=dict(type='str'),
            arguments=dict(type='str', aliases=['args']),
            runlevels=dict(type='list', elements='str'),
            daemonize=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        required_one_of=[['state', 'enabled']],
    )

    name = module.params['name']
    action = module.params['state']
    enabled = module.params['enabled']
    runlevels = module.params['runlevels']
    pattern = module.params['pattern']
    sleep_for = module.params['sleep']
    rc = 0
    out = err = ''
    result = {
        'name': name,
        'changed': False,
        'status': {}
    }

    # ensure service exists, get script name
    fail_if_missing(module, sysv_exists(name), name)
    script = get_sysv_script(name)

    # locate binaries for service management
    paths = ['/sbin', '/usr/sbin', '/bin', '/usr/bin']
    binaries = ['chkconfig', 'update-rc.d', 'insserv', 'service']

    # Keeps track of the service status for various runlevels because we can
    # operate on multiple runlevels at once
    runlevel_status = {}

    location = {}
    for binary in binaries:
        location[binary] = module.get_bin_path(binary, opt_dirs=paths)

    # figure out enable status
    if runlevels:
        for rl in runlevels:
            runlevel_status.setdefault(rl, {})
            runlevel_status[rl]["enabled"] = sysv_is_enabled(name, runlevel=rl)
    else:
        runlevel_status["enabled"] = sysv_is_enabled(name)

    # figure out started status, everyone does it different!
    is_started = False
    worked = False

    # user knows other methods fail and supplied pattern
    if pattern:
        worked = is_started = get_ps(module, pattern)
    else:
        if location.get('service'):
            # standard tool that has been 'destandardized' by reimplementation in other OS/distros
            cmd = '%s %s status' % (location['service'], name)
        elif script:
            # maybe script implements status (not LSB)
            cmd = '%s status' % script
        else:
            module.fail_json(msg="Unable to determine service status")

        (rc, out, err) = module.run_command(cmd)
        if not rc == -1:
            # special case
            if name == 'iptables' and "ACCEPT" in out:
                worked = True
                is_started = True

            # check output messages, messy but sadly more reliable than rc
            if not worked and out.count('\n') <= 1:

                cleanout = out.lower().replace(name.lower(), '')

                for stopped in ['stop', 'is dead ', 'dead but ', 'could not access pid file', 'inactive']:
                    if stopped in cleanout:
                        worked = True
                        break

                if not worked:
                    for started_status in ['run', 'start', 'active']:
                        if started_status in cleanout and "not " not in cleanout:
                            is_started = True
                            worked = True
                            break

            # hope rc is not lying to us, use often used 'bad' returns
            if not worked and rc in [1, 2, 3, 4, 69]:
                worked = True

        if not worked:
            # hail mary
            if rc == 0:
                is_started = True
                worked = True
            # ps for luck, can only assure positive match
            elif get_ps(module, name):
                is_started = True
                worked = True
                module.warn("Used ps output to match service name and determine it is up, this is very unreliable")

    if not worked:
        module.warn("Unable to determine if service is up, assuming it is down")

    ###########################################################################
    # BEGIN: Enable/Disable
    result['status'].setdefault('enabled', {})
    result['status']['enabled']['changed'] = False
    result['status']['enabled']['rc'] = None
    result['status']['enabled']['stdout'] = None
    result['status']['enabled']['stderr'] = None
    if runlevels:
        result['status']['enabled']['runlevels'] = runlevels
        for rl in runlevels:
            if enabled != runlevel_status[rl]["enabled"]:
                result['changed'] = True
                result['status']['enabled']['changed'] = True

        if not module.check_mode and result['changed']:
            # Perform enable/disable here
            if enabled:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s enable %s" % (location['update-rc.d'], name, ' '.join(runlevels)))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s --level %s %s on" % (location['chkconfig'], ''.join(runlevels), name))
            else:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s disable %s" % (location['update-rc.d'], name, ' '.join(runlevels)))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s --level %s %s off" % (location['chkconfig'], ''.join(runlevels), name))
    else:
        if enabled is not None and enabled != runlevel_status["enabled"]:
            result['changed'] = True
            result['status']['enabled']['changed'] = True

        if not module.check_mode and result['changed']:
            # Perform enable/disable here
            if enabled:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s defaults" % (location['update-rc.d'], name))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s %s on" % (location['chkconfig'], name))
            else:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s disable" % (location['update-rc.d'], name))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s %s off" % (location['chkconfig'], name))

    # Assigned above, might be useful is something goes sideways
    if not module.check_mode and result['status']['enabled']['changed']:
        result['status']['enabled']['rc'] = rc
        result['status']['enabled']['stdout'] = out
        result['status']['enabled']['stderr'] = err
        rc, out, err = None, None, None

        if "illegal runlevel specified" in result['status']['enabled']['stderr']:
            module.fail_json(msg="Illegal runlevel specified for enable operation on service %s" % name, **result)
    # END: Enable/Disable
    ###########################################################################

    ###########################################################################
    # BEGIN: state
    result['status'].setdefault(module.params['state'], {})
    result['status'][module.params['state']]['changed'] = False
    result['status'][module.params['state']]['rc'] = None
    result['status'][module.params['state']]['stdout'] = None
    result['status'][module.params['state']]['stderr'] = None
    if action:
        action = re.sub(r'p?ed$', '', action.lower())

        def runme(doit):

            args = module.params['arguments']
            cmd = "%s %s %s" % (script, doit, "" if args is None else args)

            # how to run
            if module.params['daemonize']:
                (rc, out, err) = daemonize(module, cmd)
            else:
                (rc, out, err) = module.run_command(cmd)
            # FIXME: ERRORS

            if rc != 0:
                module.fail_json(msg="Failed to %s service: %s" % (action, name), rc=rc, stdout=out, stderr=err)

            return (rc, out, err)

        if action == 'restart':
            result['changed'] = True
            result['status'][module.params['state']]['changed'] = True
            if not module.check_mode:

                # cannot rely on existing 'restart' in init script
                for dothis in ['stop', 'start']:
                    (rc, out, err) = runme(dothis)
                    if sleep_for:
                        sleep(sleep_for)

        elif is_started != (action == 'start'):
            result['changed'] = True
            result['status'][module.params['state']]['changed'] = True
            if not module.check_mode:
                rc, out, err = runme(action)

        elif is_started == (action == 'stop'):
            result['changed'] = True
            result['status'][module.params['state']]['changed'] = True
            if not module.check_mode:
                rc, out, err = runme(action)

        if not module.check_mode and result['status'][module.params['state']]['changed']:
            result['status'][module.params['state']]['rc'] = rc
            result['status'][module.params['state']]['stdout'] = out
            result['status'][module.params['state']]['stderr'] = err
            rc, out, err = None, None, None
    # END: state
    ###########################################################################

    module.exit_json(**result)
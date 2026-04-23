def main():
    # initialize
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', aliases=['service', 'unit']),
            state=dict(type='str', choices=['reloaded', 'restarted', 'started', 'stopped']),
            enabled=dict(type='bool'),
            force=dict(type='bool'),
            masked=dict(type='bool'),
            daemon_reload=dict(type='bool', default=False, aliases=['daemon-reload']),
            daemon_reexec=dict(type='bool', default=False, aliases=['daemon-reexec']),
            scope=dict(type='str', default='system', choices=['system', 'user', 'global']),
            no_block=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        required_one_of=[['state', 'enabled', 'masked', 'daemon_reload', 'daemon_reexec']],
        required_by=dict(
            state=('name', ),
            enabled=('name', ),
            masked=('name', ),
        ),
    )

    unit = module.params['name']
    if unit is not None:
        for globpattern in (r"*", r"?", r"["):
            if globpattern in unit:
                module.fail_json(msg="This module does not currently support using glob patterns, found '%s' in service name: %s" % (globpattern, unit))

    systemctl = module.get_bin_path('systemctl', True)

    if os.getenv('XDG_RUNTIME_DIR') is None:
        os.environ['XDG_RUNTIME_DIR'] = '/run/user/%s' % os.geteuid()

    # Set CLI options depending on params
    # if scope is 'system' or None, we can ignore as there is no extra switch.
    # The other choices match the corresponding switch
    if module.params['scope'] != 'system':
        systemctl += " --%s" % module.params['scope']

    if module.params['no_block']:
        systemctl += " --no-block"

    if module.params['force']:
        systemctl += " --force"

    rc = 0
    out = err = ''
    result = dict(
        name=unit,
        changed=False,
        status=dict(),
    )

    # Run daemon-reload first, if requested
    if module.params['daemon_reload'] and not module.check_mode:
        (rc, out, err) = module.run_command("%s daemon-reload" % (systemctl))
        if rc != 0:
            if is_chroot(module) or os.environ.get('SYSTEMD_OFFLINE') == '1':
                module.warn('daemon-reload failed, but target is a chroot or systemd is offline. Continuing. Error was: %d / %s' % (rc, err))
            else:
                module.fail_json(msg='failure %d during daemon-reload: %s' % (rc, err))

    # Run daemon-reexec
    if module.params['daemon_reexec'] and not module.check_mode:
        (rc, out, err) = module.run_command("%s daemon-reexec" % (systemctl))
        if rc != 0:
            if is_chroot(module) or os.environ.get('SYSTEMD_OFFLINE') == '1':
                module.warn('daemon-reexec failed, but target is a chroot or systemd is offline. Continuing. Error was: %d / %s' % (rc, err))
            else:
                module.fail_json(msg='failure %d during daemon-reexec: %s' % (rc, err))

    if unit:
        found = False
        is_initd = sysv_exists(unit)
        is_systemd = False

        # check service data, cannot error out on rc as it changes across versions, assume not found
        (rc, out, err) = module.run_command("%s show '%s'" % (systemctl, unit))

        if rc == 0 and not (request_was_ignored(out) or request_was_ignored(err)):
            # load return of systemctl show into dictionary for easy access and return
            if out:
                result['status'] = parse_systemctl_show(to_native(out).split('\n'))

                is_systemd = 'LoadState' in result['status'] and result['status']['LoadState'] != 'not-found'

                is_masked = 'LoadState' in result['status'] and result['status']['LoadState'] == 'masked'

                # Check for loading error
                if is_systemd and not is_masked and 'LoadError' in result['status']:
                    module.fail_json(msg="Error loading unit file '%s': %s" % (unit, result['status']['LoadError']))

        # Workaround for https://github.com/ansible/ansible/issues/71528
        elif err and rc == 1 and 'Failed to parse bus message' in err:
            result['status'] = parse_systemctl_show(to_native(out).split('\n'))

            unit_base, sep, suffix = unit.partition('@')
            unit_search = '{unit_base}{sep}'.format(unit_base=unit_base, sep=sep)
            (rc, out, err) = module.run_command("{systemctl} list-unit-files '{unit_search}*'".format(systemctl=systemctl, unit_search=unit_search))
            is_systemd = unit_search in out

            (rc, out, err) = module.run_command("{systemctl} is-active '{unit}'".format(systemctl=systemctl, unit=unit))
            result['status']['ActiveState'] = out.rstrip('\n')

        else:
            # list taken from man systemctl(1) for systemd 244
            valid_enabled_states = [
                "enabled",
                "enabled-runtime",
                "linked",
                "linked-runtime",
                "masked",
                "masked-runtime",
                "static",
                "indirect",
                "disabled",
                "generated",
                "transient"]

            (rc, out, err) = module.run_command("%s is-enabled '%s'" % (systemctl, unit))
            if out.strip() in valid_enabled_states:
                is_systemd = True
            else:
                # fallback list-unit-files as show does not work on some systems (chroot)
                # not used as primary as it skips some services (like those using init.d) and requires .service/etc notation
                (rc, out, err) = module.run_command("%s list-unit-files '%s'" % (systemctl, unit))
                if rc == 0:
                    is_systemd = True
                else:
                    # Check for systemctl command
                    module.run_command(systemctl, check_rc=True)

        # Does service exist?
        found = is_systemd or is_initd
        if is_initd and not is_systemd:
            module.warn('The service (%s) is actually an init script but the system is managed by systemd' % unit)

        # mask/unmask the service, if requested, can operate on services before they are installed
        if module.params['masked'] is not None:
            # state is not masked unless systemd affirms otherwise
            (rc, out, err) = module.run_command("%s is-enabled '%s'" % (systemctl, unit))
            masked = out.strip() == "masked"

            if masked != module.params['masked']:
                result['changed'] = True
                if module.params['masked']:
                    action = 'mask'
                else:
                    action = 'unmask'

                if not module.check_mode:
                    (rc, out, err) = module.run_command("%s %s '%s'" % (systemctl, action, unit))
                    if rc != 0:
                        # some versions of system CAN mask/unmask non existing services, we only fail on missing if they don't
                        fail_if_missing(module, found, unit, msg='host')
                        # here if service was not missing, but failed for other reasons
                        module.fail_json(msg=f"Failed to {action} the service ({unit}): {err.strip()}")

        # Enable/disable service startup at boot if requested
        if module.params['enabled'] is not None:

            if module.params['enabled']:
                action = 'enable'
            else:
                action = 'disable'

            fail_if_missing(module, found, unit, msg='host')

            # do we need to enable the service?
            enabled = False
            (rc, out, err) = module.run_command("%s is-enabled '%s' -l" % (systemctl, unit))

            # check systemctl result or if it is a init script
            if rc == 0:
                # https://www.freedesktop.org/software/systemd/man/systemctl.html#is-enabled%20UNIT%E2%80%A6
                if out.rstrip() in (
                        "enabled-runtime",  # transiently enabled but we're trying to set a permanent enabled
                        "indirect",  # We've been asked to enable this unit so do so despite possible reasons
                                     # that systemctl may have for thinking it's enabled already.
                        "alias"):  # Let systemd handle the alias as we can't be sure what's needed.
                    enabled = False
                else:
                    enabled = True
            elif rc == 1:
                # if not a user or global user service and both init script and unit file exist stdout should have enabled/disabled, otherwise use rc entries
                if module.params['scope'] == 'system' and \
                        is_initd and \
                        not out.strip().endswith('disabled') and \
                        sysv_is_enabled(unit):
                    enabled = True

            # default to current state
            result['enabled'] = enabled

            # Change enable/disable if needed
            if enabled != module.params['enabled']:
                result['changed'] = True
                if not module.check_mode:
                    (rc, out, err) = module.run_command("%s %s '%s'" % (systemctl, action, unit))
                    if rc != 0:
                        module.fail_json(msg="Unable to %s service %s: %s" % (action, unit, out + err))

                result['enabled'] = not enabled

        # set service state if requested
        if module.params['state'] is not None:
            fail_if_missing(module, found, unit, msg="host")

            # default to desired state
            result['state'] = module.params['state']

            # What is current service state?
            if 'ActiveState' in result['status']:
                action = None
                if module.params['state'] == 'started':
                    if not is_running_service(result['status']):
                        action = 'start'
                elif module.params['state'] == 'stopped':
                    if is_running_service(result['status']) or is_deactivating_service(result['status']):
                        action = 'stop'
                else:
                    if not is_running_service(result['status']):
                        action = 'start'
                    else:
                        action = module.params['state'][:-2]  # remove 'ed' from restarted/reloaded
                    result['state'] = 'started'

                if action:
                    result['changed'] = True
                    if not module.check_mode:
                        (rc, out, err) = module.run_command("%s %s '%s'" % (systemctl, action, unit))
                        if rc != 0:
                            module.fail_json(msg="Unable to %s service %s: %s" % (action, unit, err))
            # check for chroot
            elif is_chroot(module) or os.environ.get('SYSTEMD_OFFLINE') == '1':
                module.warn("Target is a chroot or systemd is offline. This can lead to false positives or prevent the init system tools from working.")
            else:
                # this should not happen?
                module.fail_json(msg="Service is in unknown state", status=result['status'])

    module.exit_json(**result)
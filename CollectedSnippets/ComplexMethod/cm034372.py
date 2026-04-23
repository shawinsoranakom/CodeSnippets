def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            table=dict(type='str', default='filter', choices=['filter', 'nat', 'mangle', 'raw', 'security']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            action=dict(type='str', default='append', choices=['append', 'insert']),
            ip_version=dict(type='str', default='ipv4', choices=['ipv4', 'ipv6', 'both']),
            chain=dict(type='str'),
            rule_num=dict(type='str'),
            protocol=dict(type='str'),
            wait=dict(type='str'),
            source=dict(type='str'),
            to_source=dict(type='str'),
            destination=dict(type='str'),
            to_destination=dict(type='str'),
            match=dict(type='list', elements='str', default=[]),
            tcp_flags=dict(type='dict',
                           options=dict(
                                flags=dict(type='list', elements='str'),
                                flags_set=dict(type='list', elements='str'))
                           ),
            jump=dict(type='str'),
            gateway=dict(type='str'),
            log_prefix=dict(type='str'),
            log_level=dict(type='str',
                           choices=['0', '1', '2', '3', '4', '5', '6', '7',
                                    'emerg', 'alert', 'crit', 'error',
                                    'warning', 'notice', 'info', 'debug'],
                           default=None,
                           ),
            goto=dict(type='str'),
            in_interface=dict(type='str'),
            out_interface=dict(type='str'),
            fragment=dict(type='str'),
            set_counters=dict(type='str'),
            source_port=dict(type='str'),
            destination_port=dict(type='str'),
            destination_ports=dict(type='list', elements='str', default=[]),
            to_ports=dict(type='str'),
            set_dscp_mark=dict(type='str'),
            set_dscp_mark_class=dict(type='str'),
            comment=dict(type='str'),
            ctstate=dict(type='list', elements='str', default=[]),
            src_range=dict(type='str'),
            dst_range=dict(type='str'),
            match_set=dict(type='str'),
            match_set_flags=dict(
                type='str',
                choices=['src', 'dst', 'src,dst', 'dst,src', 'src,src', 'dst,dst']
            ),
            limit=dict(type='str'),
            limit_burst=dict(type='str'),
            uid_owner=dict(type='str'),
            gid_owner=dict(type='str'),
            reject_with=dict(type='str'),
            icmp_type=dict(type='str'),
            syn=dict(type='str', default='ignore', choices=['ignore', 'match', 'negate']),
            flush=dict(type='bool', default=False),
            policy=dict(type='str', choices=['ACCEPT', 'DROP', 'QUEUE', 'RETURN']),
            chain_management=dict(type='bool', default=False),
            numeric=dict(type='bool', default=False),
        ),
        mutually_exclusive=(
            ['set_dscp_mark', 'set_dscp_mark_class'],
            ['flush', 'policy'],
        ),
        required_by=dict(
            set_dscp_mark=('jump',),
            set_dscp_mark_class=('jump',),
        ),
        required_if=[
            ['jump', 'TEE', ['gateway']],
            ['jump', 'tee', ['gateway']],
            ['flush', False, ['chain']],
        ]
    )
    args = dict(
        changed=False,
        failed=False,
        ip_version=module.params['ip_version'],
        table=module.params['table'],
        chain=module.params['chain'],
        flush=module.params['flush'],
        rule=' '.join(construct_rule(module.params)),
        state=module.params['state'],
        chain_management=module.params['chain_management'],
        wait=module.params['wait'],
    )

    ip_version = ['ipv4', 'ipv6'] if module.params['ip_version'] == 'both' else [module.params['ip_version']]
    iptables_path = [module.get_bin_path('iptables', True) if ip_version == 'ipv4' else module.get_bin_path('ip6tables', True) for ip_version in ip_version]

    both_changed = False

    for path in iptables_path:
        if module.params.get('log_prefix', None) or module.params.get('log_level', None):
            if module.params['jump'] is None:
                module.params['jump'] = 'LOG'
            elif module.params['jump'] != 'LOG':
                module.fail_json(msg="Logging options can only be used with the LOG jump target.")

        # Check if wait option is supported
        iptables_version = LooseVersion(get_iptables_version(path, module))

        if iptables_version >= LooseVersion(IPTABLES_WAIT_SUPPORT_ADDED):
            if iptables_version < LooseVersion(IPTABLES_WAIT_WITH_SECONDS_SUPPORT_ADDED):
                module.params['wait'] = ''
        else:
            module.params['wait'] = None

        # Flush the table
        if args['flush'] is True:
            args['changed'] = True
            both_changed = True
            if not module.check_mode:
                flush_table(path, module, module.params)

        # Set the policy
        elif module.params['policy']:
            current_policy = get_chain_policy(path, module, module.params)
            if not current_policy:
                module.fail_json(msg='Can\'t detect current policy')

            changed = current_policy != module.params['policy']
            args['changed'] = changed
            both_changed = both_changed or changed
            if changed and not module.check_mode:
                set_chain_policy(path, module, module.params)

        # Delete the chain if there is no rule in the arguments
        elif (args['state'] == 'absent') and not args['rule']:
            chain_is_present = check_chain_present(
                path, module, module.params
            )
            args['changed'] = chain_is_present
            both_changed = both_changed or chain_is_present

            if (chain_is_present and args['chain_management'] and not module.check_mode):
                delete_chain(path, module, module.params)

        else:
            # Create the chain if there are no rule arguments
            if (args['state'] == 'present') and not args['rule']:
                chain_is_present = check_chain_present(
                    path, module, module.params
                )
                args['changed'] = not chain_is_present
                both_changed = both_changed or not chain_is_present

                if (not chain_is_present and args['chain_management'] and not module.check_mode):
                    create_chain(path, module, module.params)

            else:
                insert = (module.params['action'] == 'insert')
                rule_is_present = check_rule_present(
                    path, module, module.params
                )

                should_be_present = (args['state'] == 'present')
                # Check if target is up to date
                args['changed'] = (rule_is_present != should_be_present)
                both_changed = both_changed or (rule_is_present != should_be_present)
                if args['changed'] is False:
                    # Target is already up to date
                    continue

                # Modify if not check_mode
                if not module.check_mode:
                    if should_be_present:
                        if insert:
                            insert_rule(path, module, module.params)
                        else:
                            append_rule(path, module, module.params)
                    else:
                        remove_rule(path, module, module.params)

    args['changed'] = both_changed

    module.exit_json(**args)
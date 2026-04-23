def main():
    module = AnsibleModule(
        argument_spec=dict(
            database=dict(type='str', required=True),
            key=dict(type='str', no_log=False),
            service=dict(type='str'),
            split=dict(type='str'),
            fail_key=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    colon = ['passwd', 'shadow', 'group', 'gshadow']

    database = module.params['database']
    key = module.params.get('key')
    split = module.params.get('split')
    service = module.params.get('service')
    fail_key = module.params.get('fail_key')

    getent_bin = module.get_bin_path('getent', True)

    if key is not None:
        cmd = [getent_bin, database, key]
    else:
        cmd = [getent_bin, database]

    if service is not None:
        cmd.extend(['-s', service])

    if not split and split is not None:
        module.fail_json(msg="Invalid split value. The value must be a non-empty string")

    if split is None and database in colon:
        split = ':'

    try:
        rc, out, err = module.run_command(cmd)
    except Exception as e:
        module.fail_json(msg=to_native(e))

    msg = "Unexpected failure!"
    dbtree = 'getent_%s' % database
    results = {dbtree: {}}

    if rc == 0:
        seen = {}
        for line in out.splitlines():
            record = line.split(split)

            if record[0] in seen:
                # more than one result for same key, ensure we store in a list
                if seen[record[0]] == 1:
                    results[dbtree][record[0]] = [results[dbtree][record[0]]]

                results[dbtree][record[0]].append(record[1:])
                seen[record[0]] += 1
            else:
                # new key/value, just assign
                results[dbtree][record[0]] = record[1:]
                seen[record[0]] = 1

        module.exit_json(ansible_facts=results)

    elif rc == 1:
        msg = "Missing arguments, or database unknown."
    elif rc == 2:
        msg = "One or more supplied key could not be found in the database."
        if not fail_key:
            results[dbtree][key] = None
            module.exit_json(ansible_facts=results, msg=msg)
    elif rc == 3:
        msg = "Enumeration not supported on this database."

    module.fail_json(msg=msg)
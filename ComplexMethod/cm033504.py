def main():
    features = [
        'extra_vars',
        'include_params',
        # 'role_params',  # FIXME: we don't yet validate tasks within a role
        'set_fact',
        # 'registered_vars',  # FIXME: hard to simulate
        'include_vars',
        # 'role_dep_params',
        'task_vars',
        'block_vars',
        'role_var',
        'vars_file',
        'play_var',
        # 'host_facts',  # FIXME: hard to simulate
        'pb_host_vars_file',
        'ini_host_vars_file',
        'ini_host',
        'pb_group_vars_file_child',
        # 'ini_group_vars_file_child', # FIXME: this contradicts documented precedence pb group vars files should override inventory ones
        'pb_group_vars_file_parent',
        'ini_group_vars_file_parent',
        'pb_group_vars_file_all',
        'ini_group_vars_file_all',
        'ini_child',
        'ini_parent',
        'ini_all',
        'role_parent_default',
        'role_default',
    ]

    parser = OptionParser()
    parser.add_option('-f', '--feature', action='append')
    parser.add_option('--use_dynamic_inventory', action='store_true')
    parser.add_option('--show_tree', action='store_true')
    parser.add_option('--show_content', action='store_true')
    parser.add_option('--show_stdout', action='store_true')
    parser.add_option('--copy_testcases_to_local_dir', action='store_true')
    (options, args) = parser.parse_args()

    if options.feature:
        for f in options.feature:
            if f not in features:
                print('%s is not a valid feature' % f)
                sys.exit(1)
        features = list(options.feature)

    fdesc = {
        'ini_host': 'host var inside the ini',
        'script_host': 'host var inside the script _meta',
        'ini_child': 'child group var inside the ini',
        'script_child': 'child group var inside the script',
        'ini_parent': 'parent group var inside the ini',
        'script_parent': 'parent group var inside the script',
        'ini_all': 'all group var inside the ini',
        'script_all': 'all group var inside the script',
        'ini_host_vars_file': 'var in inventory/host_vars/host',
        'ini_group_vars_file_parent': 'var in inventory/group_vars/parent',
        'ini_group_vars_file_child': 'var in inventory/group_vars/child',
        'ini_group_vars_file_all': 'var in inventory/group_vars/all',
        'pb_group_vars_file_parent': 'var in playbook/group_vars/parent',
        'pb_group_vars_file_child': 'var in playbook/group_vars/child',
        'pb_group_vars_file_all': 'var in playbook/group_vars/all',
        'pb_host_vars_file': 'var in playbook/host_vars/host',
        'play_var': 'var set in playbook header',
        'role_parent_default': 'var in roles/role_parent/defaults/main.yml',
        'role_default': 'var in roles/role/defaults/main.yml',
        'role_var': 'var in ???',
        'include_vars': 'var in included file',
        'set_fact': 'var made by set_fact',
        'vars_file': 'var in file added by vars_file',
        'block_vars': 'vars defined on the block',
        'task_vars': 'vars defined on the task',
        'extra_vars': 'var passed via the cli'
    }

    dinv = options.use_dynamic_inventory
    if dinv:
        # some features are specific to ini, so swap those
        for (idx, x) in enumerate(features):
            if x.startswith('ini_') and 'vars_file' not in x:
                features[idx] = x.replace('ini_', 'script_')

    dinv = options.use_dynamic_inventory

    index = 1
    while features:
        VTM = VarTestMaker(features, dynamic_inventory=dinv)
        VTM.build()

        if options.show_tree or options.show_content or options.show_stdout:
            print('')
        if options.show_tree:
            VTM.show_tree()
        if options.show_content:
            VTM.show_content()

        try:
            print("CHECKING: %s (%s)" % (features[0], fdesc.get(features[0], '')))
            res = VTM.run()
            if options.show_stdout:
                VTM.show_stdout()

            features.pop(0)

            if options.copy_testcases_to_local_dir:
                topdir = 'testcases'
                if index == 1 and os.path.isdir(topdir):
                    shutil.rmtree(topdir)
                if not os.path.isdir(topdir):
                    os.makedirs(topdir)
                thisindex = str(index)
                if len(thisindex) == 1:
                    thisindex = '0' + thisindex
                thisdir = os.path.join(topdir, '%s.%s' % (thisindex, res))
                shutil.copytree(TESTDIR, thisdir)

        except Exception as e:
            print("ERROR !!!")
            print(e)
            print('feature: %s failed' % features[0])
            sys.exit(1)
        finally:
            shutil.rmtree(TESTDIR)
            index += 1
def build(self):

        if self.dynamic_inventory:
            # python based inventory file
            self.di = DynamicInventory(self.features)
            self.di.write_script()
        else:
            # ini based inventory file
            if 'ini_host' in self.features:
                self.inventory += 'testhost findme=ini_host\n'
            else:
                self.inventory += 'testhost\n'
            self.inventory += '\n'

            if 'ini_child' in self.features:
                self.inventory += '[child]\n'
                self.inventory += 'testhost\n'
                self.inventory += '\n'
                self.inventory += '[child:vars]\n'
                self.inventory += 'findme=ini_child\n'
                self.inventory += '\n'

            if 'ini_parent' in self.features:
                if 'ini_child' in self.features:
                    self.inventory += '[parent:children]\n'
                    self.inventory += 'child\n'
                else:
                    self.inventory += '[parent]\n'
                    self.inventory += 'testhost\n'
                self.inventory += '\n'
                self.inventory += '[parent:vars]\n'
                self.inventory += 'findme=ini_parent\n'
                self.inventory += '\n'

            if 'ini_all' in self.features:
                self.inventory += '[all:vars]\n'
                self.inventory += 'findme=ini_all\n'
                self.inventory += '\n'

            # default to a single file called inventory
            invfile = os.path.join(TESTDIR, 'inventory', 'hosts')
            ipath = os.path.join(TESTDIR, 'inventory')
            if not os.path.isdir(ipath):
                os.makedirs(ipath)

            with open(invfile, 'w') as f:
                f.write(self.inventory)

        hpath = os.path.join(TESTDIR, 'inventory', 'host_vars')
        if not os.path.isdir(hpath):
            os.makedirs(hpath)
        gpath = os.path.join(TESTDIR, 'inventory', 'group_vars')
        if not os.path.isdir(gpath):
            os.makedirs(gpath)

        if 'ini_host_vars_file' in self.features:
            hfile = os.path.join(hpath, 'testhost')
            with open(hfile, 'w') as f:
                f.write('findme: ini_host_vars_file\n')

        if 'ini_group_vars_file_all' in self.features:
            hfile = os.path.join(gpath, 'all')
            with open(hfile, 'w') as f:
                f.write('findme: ini_group_vars_file_all\n')

        if 'ini_group_vars_file_child' in self.features:
            hfile = os.path.join(gpath, 'child')
            with open(hfile, 'w') as f:
                f.write('findme: ini_group_vars_file_child\n')

        if 'ini_group_vars_file_parent' in self.features:
            hfile = os.path.join(gpath, 'parent')
            with open(hfile, 'w') as f:
                f.write('findme: ini_group_vars_file_parent\n')

        if 'pb_host_vars_file' in self.features:
            os.makedirs(os.path.join(TESTDIR, 'host_vars'))
            fname = os.path.join(TESTDIR, 'host_vars', 'testhost')
            with open(fname, 'w') as f:
                f.write('findme: pb_host_vars_file\n')

        if 'pb_group_vars_file_parent' in self.features:
            if not os.path.isdir(os.path.join(TESTDIR, 'group_vars')):
                os.makedirs(os.path.join(TESTDIR, 'group_vars'))
            fname = os.path.join(TESTDIR, 'group_vars', 'parent')
            with open(fname, 'w') as f:
                f.write('findme: pb_group_vars_file_parent\n')

        if 'pb_group_vars_file_child' in self.features:
            if not os.path.isdir(os.path.join(TESTDIR, 'group_vars')):
                os.makedirs(os.path.join(TESTDIR, 'group_vars'))
            fname = os.path.join(TESTDIR, 'group_vars', 'child')
            with open(fname, 'w') as f:
                f.write('findme: pb_group_vars_file_child\n')

        if 'pb_group_vars_file_all' in self.features:
            if not os.path.isdir(os.path.join(TESTDIR, 'group_vars')):
                os.makedirs(os.path.join(TESTDIR, 'group_vars'))
            fname = os.path.join(TESTDIR, 'group_vars', 'all')
            with open(fname, 'w') as f:
                f.write('findme: pb_group_vars_file_all\n')

        if 'play_var' in self.features:
            self.playvars['findme'] = 'play_var'

        if 'set_fact' in self.features:
            self.tasks.append(dict(set_fact='findme="set_fact"'))

        if 'vars_file' in self.features:
            self.varsfiles.append('varsfile.yml')
            fname = os.path.join(TESTDIR, 'varsfile.yml')
            with open(fname, 'w') as f:
                f.write('findme: vars_file\n')

        if 'include_vars' in self.features:
            self.tasks.append(dict(include_vars='included_vars.yml'))
            fname = os.path.join(TESTDIR, 'included_vars.yml')
            with open(fname, 'w') as f:
                f.write('findme: include_vars\n')

        if 'role_var' in self.features:
            role = Role('role_var')
            role.vars = True
            role.load = True
            self.roles.append(role)

        if 'role_parent_default' in self.features:
            role = Role('role_default')
            role.load = False
            role.defaults = True
            self.roles.append(role)

            role = Role('role_parent_default')
            role.dependencies.append('role_default')
            role.defaults = True
            role.load = True
            if 'role_params' in self.features:
                role.params = dict(findme='role_params')
            self.roles.append(role)

        elif 'role_default' in self.features:
            role = Role('role_default')
            role.defaults = True
            role.load = True
            if 'role_params' in self.features:
                role.params = dict(findme='role_params')
            self.roles.append(role)

        debug_task = dict(debug='var=findme')
        test_task = {'assert': dict(that=['findme == "%s"' % self.features[0]])}
        if 'task_vars' in self.features:
            test_task['vars'] = dict(findme="task_vars")
        if 'registered_vars' in self.features:
            test_task['register'] = 'findme'

        if 'block_vars' in self.features:
            block_wrapper = [
                debug_task,
                {
                    'block': [test_task],
                    'vars': dict(findme="block_vars"),
                }
            ]
        else:
            block_wrapper = [debug_task, test_task]

        if 'include_params' in self.features:
            self.tasks.append(dict(name='including tasks', include_tasks='included_tasks.yml', vars=dict(findme='include_params')))
        else:
            self.tasks.append(dict(include_tasks='included_tasks.yml'))

        fname = os.path.join(TESTDIR, 'included_tasks.yml')
        with open(fname, 'w') as f:
            f.write(yaml.dump(block_wrapper))

        self.write_playbook()
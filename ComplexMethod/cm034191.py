def run(self):
        """ create and execute the single task playbook """

        super(AdHocCLI, self).run()

        # only thing left should be host pattern
        pattern = to_text(context.CLIARGS['args'], errors='surrogate_or_strict')

        # handle password prompts
        sshpass = None
        becomepass = None

        (sshpass, becomepass) = self.ask_passwords()
        passwords = {'conn_pass': sshpass, 'become_pass': becomepass}

        # get basic objects
        loader, inventory, variable_manager = self._play_prereqs()

        # get list of hosts to execute against
        try:
            hosts = self.get_host_list(inventory, context.CLIARGS['subset'], pattern)
        except AnsibleError:
            if context.CLIARGS['subset']:
                raise
            else:
                hosts = []
                display.warning("No hosts matched, nothing to do")

        # just listing hosts?
        if context.CLIARGS['listhosts']:
            display.display('  hosts (%d):' % len(hosts))
            for host in hosts:
                display.display('    %s' % host)
            return 0

        # verify we have arguments if we know we need em
        if context.CLIARGS['module_name'] in C.MODULE_REQUIRE_ARGS and not context.CLIARGS['module_args']:
            err = "No argument passed to %s module" % context.CLIARGS['module_name']
            if pattern.endswith(".yml"):
                err = err + ' (did you mean to run ansible-playbook?)'
            raise AnsibleOptionsError(err)

        # Avoid modules that don't work with ad-hoc
        if context.CLIARGS['module_name'] in C._ACTION_IMPORT_PLAYBOOK:
            raise AnsibleOptionsError("'%s' is not a valid action for ad-hoc commands"
                                      % context.CLIARGS['module_name'])

        # construct playbook objects to wrap task
        play_ds = self._play_ds(pattern, context.CLIARGS['seconds'], context.CLIARGS['poll_interval'])
        play = Play().load(play_ds, variable_manager=variable_manager, loader=loader)

        # used in start callback
        playbook = Playbook(loader)
        playbook._entries.append(play)
        playbook._file_name = '__adhoc_playbook__'

        if self.callback:
            cb = self.callback
        elif context.CLIARGS['one_line']:
            cb = 'oneline'
        # Respect custom 'stdout_callback' only with enabled 'bin_ansible_callbacks'
        elif C.DEFAULT_LOAD_CALLBACK_PLUGINS and C.DEFAULT_STDOUT_CALLBACK != 'default':
            cb = C.DEFAULT_STDOUT_CALLBACK
        else:
            cb = 'minimal'

        run_tree = False
        if context.CLIARGS['tree']:
            C.CALLBACKS_ENABLED.append('tree')
            C.TREE_DIR = context.CLIARGS['tree']
            run_tree = True

        # now create a task queue manager to execute the play
        self._tqm = None
        try:
            self._tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords=passwords,
                stdout_callback_name=cb,
                run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                run_tree=run_tree,
                forks=context.CLIARGS['forks'],
            )

            self._tqm.load_callbacks()
            self._tqm.send_callback('v2_playbook_on_start', playbook)

            result = self._tqm.run(play)

            self._tqm.send_callback('v2_playbook_on_stats', self._tqm._stats)
        except AnsibleEndPlay as e:
            result = e.result
        finally:
            if self._tqm:
                self._tqm.cleanup()
            if loader:
                loader.cleanup_all_tmp_files()

        return result
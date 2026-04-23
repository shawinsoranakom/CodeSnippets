def run(self):

        super(PlaybookCLI, self).run()

        # Note: slightly wrong, this is written so that implicit localhost
        # manages passwords
        sshpass = None
        becomepass = None
        passwords = {}

        # initial error check, to make sure all specified playbooks are accessible
        # before we start running anything through the playbook executor
        # also prep plugin paths
        b_playbook_dirs = []
        for playbook in context.CLIARGS['args']:

            # resolve if it is collection playbook with FQCN notation, if not, leaves unchanged
            resource = _get_collection_playbook_path(playbook)
            if resource is not None:
                playbook_collection = resource[2]
            else:
                # not an FQCN so must be a file
                if not os.path.exists(playbook):
                    raise AnsibleError("the playbook: %s could not be found" % playbook)
                if not (os.path.isfile(playbook) or stat.S_ISFIFO(os.stat(playbook).st_mode)):
                    raise AnsibleError("the playbook: %s does not appear to be a file" % playbook)

                # check if playbook is from collection (path can be passed directly)
                playbook_collection = _get_collection_name_from_path(playbook)

            # don't add collection playbooks to adjacency search path
            if not playbook_collection:
                # setup dirs to enable loading plugins from all playbooks in case they add callbacks/inventory/etc
                b_playbook_dir = os.path.dirname(os.path.abspath(to_bytes(playbook, errors='surrogate_or_strict')))
                add_all_plugin_dirs(b_playbook_dir)
                b_playbook_dirs.append(b_playbook_dir)

        if b_playbook_dirs:
            # allow collections adjacent to these playbooks
            # we use list copy to avoid opening up 'adjacency' in the previous loop
            AnsibleCollectionConfig.playbook_paths = b_playbook_dirs

        # don't deal with privilege escalation or passwords when we don't need to
        if not (context.CLIARGS['listhosts'] or context.CLIARGS['listtasks'] or
                context.CLIARGS['listtags'] or context.CLIARGS['syntax']):
            (sshpass, becomepass) = self.ask_passwords()
            passwords = {'conn_pass': sshpass, 'become_pass': becomepass}

        # create base objects
        loader, inventory, variable_manager = self._play_prereqs()

        # (which is not returned in list_hosts()) is taken into account for
        # warning if inventory is empty.  But it can't be taken into account for
        # checking if limit doesn't match any hosts.  Instead we don't worry about
        # limit if only implicit localhost was in inventory to start with.
        #
        # Fix this when we rewrite inventory by making localhost a real host (and thus show up in list_hosts())
        CLI.get_host_list(inventory, context.CLIARGS['subset'])

        # create the playbook executor, which manages running the plays via a task queue manager
        pbex = PlaybookExecutor(playbooks=context.CLIARGS['args'], inventory=inventory,
                                variable_manager=variable_manager, loader=loader,
                                passwords=passwords)

        results = pbex.run()

        if isinstance(results, list):
            for p in results:

                display.display('\nplaybook: %s' % p['playbook'])
                for idx, play in enumerate(p['plays']):
                    if play._included_path is not None:
                        loader.set_basedir(play._included_path)
                    else:
                        pb_dir = os.path.realpath(os.path.dirname(p['playbook']))
                        loader.set_basedir(pb_dir)

                    # show host list if we were able to template into a list
                    try:
                        host_list = ','.join(play.hosts)
                    except TypeError:
                        host_list = ''

                    msg = "\n  play #%d (%s): %s" % (idx + 1, host_list, play.name)
                    mytags = set(play.tags)
                    msg += '\tTAGS: [%s]' % (','.join(mytags))

                    if context.CLIARGS['listhosts']:
                        playhosts = set(inventory.get_hosts(play.hosts))
                        msg += "\n    pattern: %s\n    hosts (%d):" % (play.hosts, len(playhosts))
                        for host in playhosts:
                            msg += "\n      %s" % host

                    display.display(msg)

                    all_tags = set()
                    if context.CLIARGS['listtags'] or context.CLIARGS['listtasks']:
                        taskmsg = ''
                        if context.CLIARGS['listtasks']:
                            taskmsg = '    tasks:\n'

                        def _process_block(b):
                            taskmsg = ''
                            for task in b.block:
                                if isinstance(task, Block):
                                    taskmsg += _process_block(task)
                                else:
                                    if task.action in C._ACTION_META and task.implicit:
                                        continue

                                    all_tags.update(task.tags)
                                    if context.CLIARGS['listtasks']:
                                        cur_tags = list(mytags.union(set(task.tags)))
                                        cur_tags.sort()
                                        if task.name:
                                            taskmsg += "      %s" % task.get_name()
                                        else:
                                            taskmsg += "      %s" % task.action
                                        taskmsg += "\tTAGS: [%s]\n" % ', '.join(cur_tags)

                            return taskmsg

                        all_vars = variable_manager.get_vars(play=play)
                        for block in play.compile():
                            block = block.filter_tagged_tasks(all_vars)
                            if not block.has_tasks():
                                continue
                            taskmsg += _process_block(block)

                        if context.CLIARGS['listtags']:
                            cur_tags = list(mytags.union(all_tags))
                            cur_tags.sort()
                            taskmsg += "      TASK TAGS: [%s]\n" % ', '.join(cur_tags)

                        display.display(taskmsg)

            return 0
        else:
            return results
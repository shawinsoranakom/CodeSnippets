def run(self):
        """
        Run the given playbook, based on the settings in the play which
        may limit the runs to serialized groups, etc.
        """

        result = 0
        entrylist = []
        entry = {}
        try:
            # preload become/connection/shell to set config defs cached
            list(connection_loader.all(class_only=True))
            list(shell_loader.all(class_only=True))
            list(become_loader.all(class_only=True))

            for playbook in self._playbooks:

                # deal with FQCN
                resource = _get_collection_playbook_path(playbook)
                if resource is not None:
                    playbook_path = resource[1]
                    playbook_collection = resource[2]
                else:
                    playbook_path = playbook
                    # not fqcn, but might still be collection playbook
                    playbook_collection = _get_collection_name_from_path(playbook)

                if playbook_collection:
                    display.v("running playbook inside collection {0}".format(playbook_collection))
                    AnsibleCollectionConfig.default_collection = playbook_collection
                else:
                    AnsibleCollectionConfig.default_collection = None

                pb = Playbook.load(playbook_path, variable_manager=self._variable_manager, loader=self._loader)
                # FIXME: move out of inventory self._inventory.set_playbook_basedir(os.path.realpath(os.path.dirname(playbook_path)))

                if self._tqm is None:  # we are doing a listing
                    entry = {'playbook': playbook_path}
                    entry['plays'] = []
                else:
                    # make sure the tqm has callbacks loaded
                    self._tqm.load_callbacks()
                    self._tqm.send_callback('v2_playbook_on_start', pb)

                i = 1
                plays = pb.get_plays()
                display.vv(u'%d plays in %s' % (len(plays), to_text(playbook_path)))

                for play in plays:
                    if play._included_path is not None:
                        self._loader.set_basedir(play._included_path)
                    else:
                        self._loader.set_basedir(pb._basedir)

                    # clear any filters which may have been applied to the inventory
                    self._inventory.remove_restriction()

                    # Allow variables to be used in vars_prompt fields.
                    all_vars = self._variable_manager.get_vars(play=play)
                    templar = TemplateEngine(loader=self._loader, variables=all_vars)
                    setattr(play, 'vars_prompt', templar.template(play.vars_prompt))

                    # FIXME: this should be a play 'sub object' like loop_control
                    if play.vars_prompt:
                        for var in play.vars_prompt:
                            vname = var['name']
                            prompt = var.get("prompt", vname)
                            default = var.get("default", None)
                            private = boolean(var.get("private", True))
                            confirm = boolean(var.get("confirm", False))
                            encrypt = var.get("encrypt", None)
                            salt_size = var.get("salt_size", None)
                            salt = var.get("salt", None)
                            unsafe = boolean(var.get("unsafe", False))

                            if vname not in self._variable_manager.extra_vars:
                                if self._tqm:
                                    self._tqm.send_callback('v2_playbook_on_vars_prompt', vname, private, prompt, encrypt, confirm, salt_size, salt,
                                                            default, unsafe)
                                    play.vars[vname] = display.do_var_prompt(vname, private, prompt, encrypt, confirm, salt_size, salt, default, unsafe)
                                else:  # we are either in --list-<option> or syntax check
                                    play.vars[vname] = default

                    # Post validate so any play level variables are templated
                    all_vars = self._variable_manager.get_vars(play=play)
                    templar = TemplateEngine(loader=self._loader, variables=all_vars)
                    play.post_validate(templar)

                    if context.CLIARGS['syntax']:
                        continue

                    if self._tqm is None:
                        # we are just doing a listing
                        entry['plays'].append(play)

                    else:
                        self._tqm._unreachable_hosts.update(self._unreachable_hosts)

                        previously_failed = len(self._tqm._failed_hosts)
                        previously_unreachable = len(self._tqm._unreachable_hosts)

                        break_play = False
                        # we are actually running plays
                        batches = self._get_serialized_batches(play)
                        if len(batches) == 0:
                            self._tqm.send_callback('v2_playbook_on_play_start', play)
                            self._tqm.send_callback('v2_playbook_on_no_hosts_matched')
                        for batch in batches:
                            # restrict the inventory to the hosts in the serialized batch
                            self._inventory.restrict_to_hosts(batch)
                            # and run it...
                            try:
                                result = self._tqm.run(play=play)
                            except AnsibleEndPlay as e:
                                result = e.result
                                break

                            # break the play if the result equals the special return code
                            if result & self._tqm.RUN_FAILED_BREAK_PLAY != 0:
                                result = self._tqm.RUN_FAILED_HOSTS
                                break_play = True

                            # check the number of failures here and break out if the entire batch failed
                            failed_hosts_count = len(self._tqm._failed_hosts) + len(self._tqm._unreachable_hosts) - \
                                (previously_failed + previously_unreachable)

                            if len(batch) == failed_hosts_count:
                                break_play = True
                                break

                            # update the previous counts so they don't accumulate incorrectly
                            # over multiple serial batches
                            previously_failed += len(self._tqm._failed_hosts) - previously_failed
                            previously_unreachable += len(self._tqm._unreachable_hosts) - previously_unreachable

                            # save the unreachable hosts from this batch
                            self._unreachable_hosts.update(self._tqm._unreachable_hosts)

                        if break_play:
                            break

                    i = i + 1  # per play

                if entry:
                    entrylist.append(entry)  # per playbook

                # send the stats callback for this playbook
                if self._tqm is not None:
                    if C.RETRY_FILES_ENABLED:
                        retries = set(self._tqm._failed_hosts.keys())
                        retries.update(self._tqm._unreachable_hosts.keys())
                        retries = sorted(retries)
                        if len(retries) > 0:
                            if C.RETRY_FILES_SAVE_PATH:
                                basedir = C.RETRY_FILES_SAVE_PATH
                            elif playbook_path:
                                basedir = os.path.dirname(os.path.abspath(playbook_path))
                            else:
                                basedir = '~/'

                            (retry_name, ext) = os.path.splitext(os.path.basename(playbook_path))
                            filename = os.path.join(basedir, "%s.retry" % retry_name)
                            if self._generate_retry_inventory(filename, retries):
                                display.display("\tto retry, use: --limit @%s\n" % filename)

                    self._tqm.send_callback('v2_playbook_on_stats', self._tqm._stats)

                # if the last result wasn't zero, break out of the playbook file name loop
                if result != 0:
                    break

            if entrylist:
                return entrylist

        finally:
            if self._tqm is not None:
                self._tqm.cleanup()
            if self._loader:
                self._loader.cleanup_all_tmp_files()

        if context.CLIARGS['syntax']:
            display.display("No issues encountered")
            return result

        if context.CLIARGS['start_at_task'] and not self._tqm._start_at_done:
            display.error(
                "No matching task \"%s\" found."
                " Note: --start-at-task can only follow static includes."
                % context.CLIARGS['start_at_task']
            )

        return result
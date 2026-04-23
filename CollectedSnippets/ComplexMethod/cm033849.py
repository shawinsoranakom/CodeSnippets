def run(self, play):
        """
        Iterates over the roles/tasks in a play, using the given (or default)
        strategy for queueing tasks. The default is the linear strategy, which
        operates like classic Ansible by keeping all hosts in lock-step with
        a given task (meaning no hosts move on to the next task until all hosts
        are done with the current task).
        """

        self.load_callbacks()

        all_vars = self._variable_manager.get_vars(play=play)
        templar = TemplateEngine(loader=self._loader, variables=all_vars)

        new_play = play.copy()
        new_play.post_validate(templar)
        new_play.handlers = new_play.compile_roles_handlers() + new_play.handlers

        self.hostvars = HostVars(
            inventory=self._inventory,
            variable_manager=self._variable_manager,
            loader=self._loader,
        )

        play_context = PlayContext(new_play, self.passwords, self._connection_lockfile.fileno())

        for callback_plugin in self._callback_plugins:
            callback_plugin.set_play_context(play_context)

        self.send_callback('v2_playbook_on_play_start', new_play)

        # build the iterator
        iterator = PlayIterator(
            inventory=self._inventory,
            play=new_play,
            play_context=play_context,
            variable_manager=self._variable_manager,
            all_vars=all_vars,
            start_at_done=self._start_at_done,
        )

        # adjust to # of workers to configured forks or size of batch, whatever is lower
        self._initialize_processes(min(self._forks, iterator.batch_size))

        # load the specified strategy (or the default linear one)
        strategy = strategy_loader.get(new_play.strategy, self)
        if strategy is None:
            raise AnsibleError("Invalid play strategy specified: %s" % new_play.strategy, obj=play._ds)

        # Because the TQM may survive multiple play runs, we start by marking
        # any hosts as failed in the iterator here which may have been marked
        # as failed in previous runs. Then we clear the internal list of failed
        # hosts so we know what failed this round.
        for host_name in self._failed_hosts.keys():
            host = self._inventory.get_host(host_name)
            iterator.mark_host_failed(host)
        for host_name in self._unreachable_hosts.keys():
            iterator._play._removed_hosts.append(host_name)

        self.clear_failed_hosts()

        # during initialization, the PlayContext will clear the start_at_task
        # field to signal that a matching task was found, so check that here
        # and remember it so we don't try to skip tasks on future plays
        if context.CLIARGS.get('start_at_task') is not None and play_context.start_at_task is None:
            self._start_at_done = True

        # and run the play using the strategy and cleanup on way out
        try:
            with _strategy.StrategyContext(strategy=strategy, tqm=self).activate():
                play_return = strategy.run(iterator, play_context)
        finally:
            strategy.cleanup()
            self._cleanup_processes()

        # now re-save the hosts that failed from the iterator to our internal list
        for host_name in iterator.get_failed_hosts():
            self._failed_hosts[host_name] = True

        if iterator.end_play:
            raise AnsibleEndPlay(play_return)

        return play_return
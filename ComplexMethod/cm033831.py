def __init__(self, inventory, play, play_context, variable_manager, all_vars, start_at_done=False):
        self._play = play
        self._blocks = []
        self._variable_manager = variable_manager

        setup_block = Block(play=self._play)
        # Gathering facts with run_once would copy the facts from one host to
        # the others.
        setup_block.run_once = False
        setup_task = Task(block=setup_block)
        setup_task.action = 'gather_facts'
        setup_task.name = 'Gathering Facts'
        setup_task.args = {}

        # Unless play is specifically tagged, gathering should 'always' run
        if not self._play.tags:
            setup_task.tags = ['always']

        # Default options to gather
        for option in ('gather_subset', 'gather_timeout', 'fact_path'):
            value = getattr(self._play, option, None)
            if value is not None:
                setup_task.args[option] = value

        setup_task.set_loader(self._play._loader)
        # short circuit fact gathering if the entire playbook is conditional
        if self._play._included_conditional is not None:
            setup_task.when = self._play._included_conditional[:]
        setup_block.block = [setup_task]

        validation_task = Task.load({
            'name': f'Validating arguments against arg spec {self._play.validate_argspec}',
            'action': 'ansible.builtin.validate_argument_spec',
            'args': {
                # 'provided_arguments': {},  # allow configuration via module_defaults
                'argument_spec': self._play.argument_spec,
                'validate_args_context': {
                    'type': 'play',
                    'name': self._play.validate_argspec,
                    'argument_spec_name': self._play.validate_argspec,
                    'path': self._play._metadata_path,
                },
            },
            'tags': ['always'] if not self._play.tags else [],
        }, block=setup_block)

        validation_task.set_loader(self._play._loader)
        if self._play._included_conditional is not None:
            validation_task.when = self._play._included_conditional[:]
        setup_block.block.append(validation_task)

        setup_block = setup_block.filter_tagged_tasks(all_vars)
        self._blocks.append(setup_block)

        # keep flatten (no blocks) list of all tasks from the play
        # used for the lockstep mechanism in the linear strategy
        self.all_tasks = setup_block.get_tasks()

        for block in self._play.compile():
            new_block = block.filter_tagged_tasks(all_vars)
            if new_block.has_tasks():
                self._blocks.append(new_block)
                self.all_tasks.extend(new_block.get_tasks())

        # keep list of all handlers, it is copied into each HostState
        # at the beginning of IteratingStates.HANDLERS
        # the copy happens at each flush in order to restore the original
        # list and remove any included handlers that might not be notified
        # at the particular flush
        self.handlers = [h for b in self._play.handlers for h in b.block]

        self._host_states = {}
        start_at_matched = False
        batch = inventory.get_hosts(self._play.hosts, order=self._play.order)
        self.batch_size = len(batch)
        for host in batch:
            self.set_state_for_host(host.name, HostState(blocks=self._blocks))
            # if we're looking to start at a specific task, iterate through
            # the tasks for this host until we find the specified task
            if play_context.start_at_task is not None and not start_at_done:
                while True:
                    (s, task) = self.get_next_task_for_host(host, peek=True)
                    if s.run_state == IteratingStates.COMPLETE:
                        break
                    if task.name == play_context.start_at_task or (task.name and fnmatch.fnmatch(task.name, play_context.start_at_task)) or \
                       task.get_name() == play_context.start_at_task or fnmatch.fnmatch(task.get_name(), play_context.start_at_task):
                        start_at_matched = True
                        break
                    self.set_state_for_host(host.name, s)

                # finally, reset the host's state to IteratingStates.SETUP
                if start_at_matched:
                    self._host_states[host.name].did_start_at_task = True
                    self._host_states[host.name].run_state = IteratingStates.SETUP

        if start_at_matched:
            # we have our match, so clear the start_at_task field on the
            # play context to flag that we've started at a task (and future
            # plays won't try to advance)
            play_context.start_at_task = None

        self.end_play = False
        self.cur_task = 0
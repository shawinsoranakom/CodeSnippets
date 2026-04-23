def _postprocess_options(self):
        self._runtime_options.clear()

        # check for mutualy exclusive / dependant options
        if self.options['syslog'] and self.options['logfile']:
            self.parser.error("the syslog and logfile options are exclusive")

        if self.options['overwrite_existing_translations'] and not self['update']:
            self.parser.error("the i18n-overwrite option cannot be used without the update option")

        if len(self['db_name']) > 1 and (self['init'] or self['update']):
            self.parser.error("Cannot use -i/--init or -u/--update with multiple databases in the -d/--database/db_name")

        # ensure default server wide modules are present
        if not self['server_wide_modules']:
            self._runtime_options['server_wide_modules'] = DEFAULT_SERVER_WIDE_MODULES
        for mod in REQUIRED_SERVER_WIDE_MODULES:
            if mod not in self['server_wide_modules']:
                self._log(logging.INFO, "adding missing %r to %s", mod, self.options_index['server_wide_modules'])
                self._runtime_options['server_wide_modules'] = [mod] + self['server_wide_modules']

        # accumulate all log_handlers
        self._runtime_options['log_handler'] = list(_deduplicate_loggers([
            *self._default_options.get('log_handler', []),
            *self._file_options.get('log_handler', []),
            *self._env_options.get('log_handler', []),
            *self._cli_options.get('log_handler', []),
        ]))

        self._runtime_options['init'] = dict.fromkeys(self['init'], True) or {}
        self._runtime_options['update'] = {'base': True} if 'all' in self['update'] else dict.fromkeys(self['update'], True)

        # TODO saas-22.1: remove support for the empty db_replica_host
        if self['db_replica_host'] == '':
            self._runtime_options['db_replica_host'] = None
            if 'replica' not in self['dev_mode']:
                # Conditional warning so it is possible to have a single
                # config file (with db_replica_host= dev_mode=replica)
                # that works in both 18.0 and 19.0.
                # TODO saas-21.1:
                #   move this warning out of the if, as 18.0 won't be
                #   supported anymore, so people remove db_replica_host=
                #   from their config.
                self._warn((
                    "Since 19.0, an empty {replica_host} was the 18.0 "
                    "way to open a replica connection on the same "
                    "server as {db_host}, for development/testing "
                    "purpose, the feature now exists as {dev}=replica"
                ).format(
                    replica_host=self.options_index['db_replica_host'],
                    db_host=self.options_index['db_host'],
                    dev=self.options_index['dev_mode'],
                ), DeprecationWarning)
                self._runtime_options['dev_mode'] = self['dev_mode'] + ['replica']

        if 'all' in self['dev_mode']:
            self._runtime_options['dev_mode'] = self['dev_mode'] + ALL_DEV_MODE

        if test_file := self['test_file']:
            if not os.path.isfile(test_file):
                self._log(logging.WARNING, f'test file {test_file!r} cannot be found')
            elif not test_file.endswith('.py'):
                self._log(logging.WARNING, f'test file {test_file!r} is not a python file')
            else:
                self._log(logging.INFO, 'Transforming --test-file into --test-tags')
                test_tags = (self['test_tags'] or '').split(',')
                test_tags.append(os.path.abspath(self['test_file']))
                self._runtime_options['test_tags'] = ','.join(test_tags)
                self._runtime_options['test_enable'] = True
        if self['test_enable'] and not self['test_tags']:
            self._runtime_options['test_tags'] = "+standard"
        self._runtime_options['test_enable'] = bool(self['test_tags'])
        if self._runtime_options['test_enable']:
            self._runtime_options['stop_after_init'] = True
            if not self['db_name']:
                self._log(logging.WARNING,
                    "Empty %s, tests won't run", self.options_index['db_name'])
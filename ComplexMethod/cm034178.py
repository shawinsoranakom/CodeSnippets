def run(self):

        super(ConfigCLI, self).run()

        # initialize each galaxy server's options from known listed servers
        self._galaxy_servers = [s for s in C.GALAXY_SERVER_LIST or [] if s]  # clean list, reused later here
        C.config.load_galaxy_server_defs(self._galaxy_servers)

        if context.CLIARGS['config_file']:
            self.config_file = unfrackpath(context.CLIARGS['config_file'], follow=False)
            b_config = to_bytes(self.config_file)
            if os.path.exists(b_config) and os.access(b_config, os.R_OK):
                self.config = ConfigManager(self.config_file)
            else:
                raise AnsibleOptionsError('The provided configuration file is missing or not accessible: %s' % to_native(self.config_file))
        else:
            self.config = C.config
            self.config_file = self.config._config_file

        if self.config_file:
            try:
                if not os.path.exists(self.config_file):
                    raise AnsibleOptionsError("%s does not exist or is not accessible" % (self.config_file))
                elif not os.path.isfile(self.config_file):
                    raise AnsibleOptionsError("%s is not a valid file" % (self.config_file))

                os.environ['ANSIBLE_CONFIG'] = to_native(self.config_file)
            except Exception:
                if context.CLIARGS['action'] in ['view']:
                    raise

        elif context.CLIARGS['action'] == 'view':
            raise AnsibleError('Invalid or no config file was supplied')

        # run the requested action
        context.CLIARGS['func']()
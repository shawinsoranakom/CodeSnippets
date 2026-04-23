def run(self):

        super(ConsoleCLI, self).run()

        sshpass = None
        becomepass = None

        # hosts
        self.pattern = context.CLIARGS['pattern']
        self.cwd = self.pattern

        # Defaults from the command line
        self.remote_user = context.CLIARGS['remote_user']
        self.become = context.CLIARGS['become']
        self.become_user = context.CLIARGS['become_user']
        self.become_method = context.CLIARGS['become_method']
        self.check_mode = context.CLIARGS['check']
        self.diff = context.CLIARGS['diff']
        self.forks = context.CLIARGS['forks']
        self.task_timeout = context.CLIARGS['task_timeout']

        # set module path if needed
        if context.CLIARGS['module_path']:
            for path in context.CLIARGS['module_path']:
                if path:
                    module_loader.add_directory(path)

        # dynamically add 'canonical' modules as commands, aliases could be used and dynamically loaded
        self.modules = self.list_modules()
        for module in self.modules:
            setattr(self, 'do_' + module, lambda arg, module=module: self.default(module + ' ' + arg))
            setattr(self, 'help_' + module, lambda module=module: self.helpdefault(module))

        (sshpass, becomepass) = self.ask_passwords()
        self.passwords = {'conn_pass': sshpass, 'become_pass': becomepass}

        self.loader, self.inventory, self.variable_manager = self._play_prereqs()

        hosts = self.get_host_list(self.inventory, context.CLIARGS['subset'], self.pattern)

        self.groups = self.inventory.list_groups()
        self.hosts = [x.name for x in hosts]

        # This hack is to work around readline issues on a mac:
        #  http://stackoverflow.com/a/7116997/541202
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

        histfile = os.path.join(os.path.expanduser("~"), ".ansible-console_history")
        try:
            readline.read_history_file(histfile)
        except OSError:
            pass

        atexit.register(readline.write_history_file, histfile)
        self.set_prompt()
        self.cmdloop()
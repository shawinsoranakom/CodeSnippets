def post_process_args(self, options):
        options = super(PullCLI, self).post_process_args(options)

        if not options.dest:
            hostname = socket.getfqdn()
            # use a hostname dependent directory, in case of $HOME on nfs
            options.dest = os.path.join(C.ANSIBLE_HOME, 'pull', hostname)

        if os.path.exists(options.dest) and not os.path.isdir(options.dest):
            raise AnsibleOptionsError("%s is not a valid or accessible directory." % options.dest)

        if options.sleep:
            try:
                secs = secrets.randbelow(int(options.sleep))
                options.sleep = secs
            except ValueError:
                raise AnsibleOptionsError("%s is not a number." % options.sleep)

        if not options.url:
            raise AnsibleOptionsError("URL for repository not specified, use -h for help")

        if options.module_name not in self.REPO_CHOICES:
            raise AnsibleOptionsError("Unsupported repo module %s, choices are %s" % (options.module_name, ','.join(self.REPO_CHOICES)))

        display.verbosity = options.verbosity
        self.validate_conflicts(options)

        return options
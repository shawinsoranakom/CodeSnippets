def post_process_args(self, options):
        """Process the command line args

        Subclasses need to implement this method.  This method validates and transforms the command
        line arguments.  It can be used to check whether conflicting values were given, whether filenames
        exist, etc.

        An implementation will look something like this::

            def post_process_args(self, options):
                options = super(MyCLI, self).post_process_args(options)
                if options.addition and options.subtraction:
                    raise AnsibleOptionsError('Only one of --addition and --subtraction can be specified')
                if isinstance(options.listofhosts, str):
                    options.listofhosts = options.listofhosts.split(',')
                return options
        """

        # process tags
        if hasattr(options, 'tags') and not options.tags:
            # optparse defaults does not do what's expected
            # More specifically, we want `--tags` to be additive. So we cannot
            # simply change C.TAGS_RUN's default to ["all"] because then passing
            # --tags foo would cause us to have ['all', 'foo']
            options.tags = ['all']
        if hasattr(options, 'tags') and options.tags:
            tags = set()
            for tag_set in options.tags:
                for tag in tag_set.split(u','):
                    tags.add(tag.strip())
            options.tags = list(tags)

        # process skip_tags
        if hasattr(options, 'skip_tags') and options.skip_tags:
            skip_tags = set()
            for tag_set in options.skip_tags:
                for tag in tag_set.split(u','):
                    skip_tags.add(tag.strip())
            options.skip_tags = list(skip_tags)

        # Make sure path argument doesn't have a backslash
        if hasattr(options, 'action') and options.action in ['install', 'download'] and hasattr(options, 'args'):
            options.args = [path.rstrip("/") for path in options.args]

        # process inventory options except for CLIs that require their own processing
        if hasattr(options, 'inventory') and not self.SKIP_INVENTORY_DEFAULTS:

            if options.inventory:

                # should always be list
                if isinstance(options.inventory, str):
                    options.inventory = [options.inventory]

                # Ensure full paths when needed
                options.inventory = [unfrackpath(opt, follow=False) if ',' not in opt else opt for opt in options.inventory]
            else:
                options.inventory = C.DEFAULT_HOST_LIST

        return options
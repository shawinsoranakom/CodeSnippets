def _prepare_arguments(self, argv):
        """Prepares arguments by:

        - removing placeholder and moving arguments after it to beginning,
          we need this to distinguish arguments from `command` with ours;

        - adding `--` before `command`, so our parse would ignore arguments
          of `command`.

        """
        if ARGUMENT_PLACEHOLDER in argv:
            index = argv.index(ARGUMENT_PLACEHOLDER)
            return argv[index + 1:] + ['--'] + argv[:index]
        elif argv and not argv[0].startswith('-') and argv[0] != '--':
            return ['--'] + argv
        else:
            return argv
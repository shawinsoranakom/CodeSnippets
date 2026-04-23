def post_process_args(self, options):
        options = super(VaultCLI, self).post_process_args(options)

        display.verbosity = options.verbosity

        if options.vault_ids:
            for vault_id in options.vault_ids:
                if u';' in vault_id:
                    raise AnsibleOptionsError("'%s' is not a valid vault id. The character ';' is not allowed in vault ids" % vault_id)

        if getattr(options, 'output_file', None) and len(options.args) > 1:
            raise AnsibleOptionsError("At most one input file may be used with the --output option")

        if options.action == 'encrypt_string':
            if '-' in options.args or options.encrypt_string_stdin_name or (not options.args and not options.encrypt_string_prompt):
                # prompting from stdin and reading from stdin are mutually exclusive, if stdin is still provided, it is ignored
                self.encrypt_string_read_stdin = True

            if options.encrypt_string_prompt and self.encrypt_string_read_stdin:
                # should only trigger if prompt + either - or encrypt string stdin name were provided
                raise AnsibleOptionsError('The --prompt option is not supported if also reading input from stdin')

        return options
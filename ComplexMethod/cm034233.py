def execute_encrypt_string(self):
        """ encrypt the supplied string using the provided vault secret """
        b_plaintext = None

        # Holds tuples (the_text, the_source_of_the_string, the variable name if its provided).
        b_plaintext_list = []

        # remove the non-option '-' arg (used to indicate 'read from stdin') from the candidate args so
        # we don't add it to the plaintext list
        args = [x for x in context.CLIARGS['args'] if x != '-']

        # We can prompt and read input, or read from stdin, but not both.
        if context.CLIARGS['encrypt_string_prompt']:
            msg = "String to encrypt: "

            name = None
            name_prompt_response = display.prompt('Variable name (enter for no name): ')

            # TODO: enforce var naming rules?
            if name_prompt_response != "":
                name = name_prompt_response

            # TODO: could prompt for which vault_id to use for each plaintext string
            #       currently, it will just be the default
            hide_input = not context.CLIARGS['show_string_input']
            if hide_input:
                msg = "String to encrypt (hidden): "
            else:
                msg = "String to encrypt:"

            prompt_response = display.prompt(msg, private=hide_input)

            if prompt_response == '':
                raise AnsibleOptionsError('The plaintext provided from the prompt was empty, not encrypting')

            b_plaintext = to_bytes(prompt_response)
            b_plaintext_list.append((b_plaintext, self.FROM_PROMPT, name))

        # read from stdin
        if self.encrypt_string_read_stdin:
            if sys.stdout.isatty():
                display.display("Reading plaintext input from stdin. (ctrl-d to end input, twice if your content does not already have a newline)", stderr=True)

            stdin_text = sys.stdin.read()
            if stdin_text == '':
                raise AnsibleOptionsError('stdin was empty, not encrypting')

            if sys.stdout.isatty() and not stdin_text.endswith("\n"):
                display.display("\n")

            b_plaintext = to_bytes(stdin_text)

            # defaults to None
            name = context.CLIARGS['encrypt_string_stdin_name']
            b_plaintext_list.append((b_plaintext, self.FROM_STDIN, name))

        # use any leftover args as strings to encrypt
        # Try to match args up to --name options
        if context.CLIARGS.get('encrypt_string_names', False):
            name_and_text_list = list(zip(context.CLIARGS['encrypt_string_names'], args))

            # Some but not enough --name's to name each var
            if len(args) > len(name_and_text_list):
                # Trying to avoid ever showing the plaintext in the output, so this warning is vague to avoid that.
                display.display('The number of --name options do not match the number of args.',
                                stderr=True)
                display.display('The last named variable will be "%s". The rest will not have'
                                ' names.' % context.CLIARGS['encrypt_string_names'][-1],
                                stderr=True)

            # Add the rest of the args without specifying a name
            for extra_arg in args[len(name_and_text_list):]:
                name_and_text_list.append((None, extra_arg))

        # if no --names are provided, just use the args without a name.
        else:
            name_and_text_list = [(None, x) for x in args]

        # Convert the plaintext text objects to bytestrings and collect
        for name_and_text in name_and_text_list:
            name, plaintext = name_and_text

            if plaintext == '':
                raise AnsibleOptionsError('The plaintext provided from the command line args was empty, not encrypting')

            b_plaintext = to_bytes(plaintext)
            b_plaintext_list.append((b_plaintext, self.FROM_ARGS, name))

        # TODO: specify vault_id per string?
        # Format the encrypted strings and any corresponding stderr output
        outputs = self._format_output_vault_strings(b_plaintext_list, vault_id=self.encrypt_vault_id)

        b_outs = []
        for output in outputs:
            err = output.get('err', None)
            out = output.get('out', '')
            if err:
                sys.stderr.write(err)
            b_outs.append(to_bytes(out))

        # The output must end with a newline to play nice with terminal representation.
        # Refs:
        # * https://stackoverflow.com/a/729795/595220
        # * https://github.com/ansible/ansible/issues/78932
        b_outs.append(b'')
        self.editor.write_data(b'\n'.join(b_outs), context.CLIARGS['output_file'] or '-')

        if sys.stdout.isatty():
            display.display("Encryption successful", stderr=True)
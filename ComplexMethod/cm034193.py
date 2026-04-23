def ask_passwords():
        """ prompt for connection and become passwords if needed """

        op = context.CLIARGS
        sshpass = None
        becomepass = None

        become_prompt_method = "BECOME" if C.AGNOSTIC_BECOME_PROMPT else op['become_method'].upper()

        try:
            become_prompt = "%s password: " % become_prompt_method
            if op['ask_pass']:
                sshpass = CLI._get_secret("SSH password: ")
                become_prompt = "%s password[defaults to SSH password]: " % become_prompt_method
            elif op['connection_password_file']:
                sshpass = CLI.get_password_from_file(op['connection_password_file'])

            if op['become_ask_pass']:
                becomepass = CLI._get_secret(become_prompt)
                if op['ask_pass'] and becomepass == '':
                    becomepass = sshpass
            elif op['become_password_file']:
                becomepass = CLI.get_password_from_file(op['become_password_file'])

        except EOFError:
            pass

        return sshpass, becomepass
def setup_vault_secrets(loader, vault_ids, vault_password_files=None,
                            ask_vault_pass=None, create_new_password=False,
                            auto_prompt=True, initialize_context=True):
        # list of tuples
        vault_secrets = []

        # Depending on the vault_id value (including how --ask-vault-pass / --vault-password-file create a vault_id)
        # we need to show different prompts. This is for compat with older Towers that expect a
        # certain vault password prompt format, so 'promp_ask_vault_pass' vault_id gets the old format.
        prompt_formats = {}

        # If there are configured default vault identities, they are considered 'first'
        # so we prepend them to vault_ids (from cli) here

        vault_password_files = vault_password_files or []
        if C.DEFAULT_VAULT_PASSWORD_FILE:
            vault_password_files.append(C.DEFAULT_VAULT_PASSWORD_FILE)

        if create_new_password:
            prompt_formats['prompt'] = ['New vault password (%(vault_id)s): ',
                                        'Confirm new vault password (%(vault_id)s): ']
            # 2.3 format prompts for --ask-vault-pass
            prompt_formats['prompt_ask_vault_pass'] = ['New Vault password: ',
                                                       'Confirm New Vault password: ']
        else:
            prompt_formats['prompt'] = ['Vault password (%(vault_id)s): ']
            # The format when we use just --ask-vault-pass needs to match 'Vault password:\s*?$'
            prompt_formats['prompt_ask_vault_pass'] = ['Vault password: ']

        vault_ids = CLI.build_vault_ids(vault_ids,
                                        vault_password_files,
                                        ask_vault_pass,
                                        auto_prompt=auto_prompt)

        last_exception = found_vault_secret = None
        for vault_id_slug in vault_ids:
            vault_id_name, vault_id_value = CLI.split_vault_id(vault_id_slug)
            if vault_id_value in ['prompt', 'prompt_ask_vault_pass']:

                # --vault-id some_name@prompt_ask_vault_pass --vault-id other_name@prompt_ask_vault_pass will be a little
                # confusing since it will use the old format without the vault id in the prompt
                built_vault_id = vault_id_name or C.DEFAULT_VAULT_IDENTITY

                # choose the prompt based on --vault-id=prompt or --ask-vault-pass. --ask-vault-pass
                # always gets the old format for Tower compatibility.
                # ie, we used --ask-vault-pass, so we need to use the old vault password prompt
                # format since Tower needs to match on that format.
                prompted_vault_secret = PromptVaultSecret(prompt_formats=prompt_formats[vault_id_value],
                                                          vault_id=built_vault_id)

                # a empty or invalid password from the prompt will warn and continue to the next
                # without erroring globally
                try:
                    prompted_vault_secret.load()
                except AnsibleError as exc:
                    display.warning('Error in vault password prompt (%s): %s' % (vault_id_name, exc))
                    raise

                found_vault_secret = True
                vault_secrets.append((built_vault_id, prompted_vault_secret))

                # update loader with new secrets incrementally, so we can load a vault password
                # that is encrypted with a vault secret provided earlier
                loader.set_vault_secrets(vault_secrets)
                continue

            # assuming anything else is a password file
            display.vvvvv('Reading vault password file: %s' % vault_id_value)
            # read vault_pass from a file
            try:
                file_vault_secret = get_file_vault_secret(filename=vault_id_value,
                                                          vault_id=vault_id_name,
                                                          loader=loader)
            except AnsibleError as exc:
                display.warning('Error getting vault password file (%s): %s' % (vault_id_name, to_text(exc)))
                last_exception = exc
                continue

            try:
                file_vault_secret.load()
            except AnsibleError as exc:
                display.warning('Error in vault password file loading (%s): %s' % (vault_id_name, to_text(exc)))
                last_exception = exc
                continue

            found_vault_secret = True
            if vault_id_name:
                vault_secrets.append((vault_id_name, file_vault_secret))
            else:
                vault_secrets.append((C.DEFAULT_VAULT_IDENTITY, file_vault_secret))

            # update loader with as-yet-known vault secrets
            loader.set_vault_secrets(vault_secrets)

        # An invalid or missing password file will error globally
        # if no valid vault secret was found.
        if last_exception and not found_vault_secret:
            raise last_exception

        if initialize_context:
            VaultSecretsContext.initialize(VaultSecretsContext(vault_secrets))

        return vault_secrets
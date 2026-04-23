def run(self):
        super(VaultCLI, self).run()
        loader = DataLoader()

        # set default restrictive umask
        old_umask = os.umask(0o077)

        vault_ids = list(context.CLIARGS['vault_ids'])

        # there are 3 types of actions, those that just 'read' (decrypt, view) and only
        # need to ask for a password once, and those that 'write' (create, encrypt) that
        # ask for a new password and confirm it, and 'read/write (rekey) that asks for the
        # old password, then asks for a new one and confirms it.

        default_vault_ids = C.DEFAULT_VAULT_IDENTITY_LIST
        vault_ids = default_vault_ids + vault_ids

        action = context.CLIARGS['action']

        # TODO: instead of prompting for these before, we could let VaultEditor
        #       call a callback when it needs it.
        if action in ['decrypt', 'view', 'rekey', 'edit']:
            vault_secrets = self.setup_vault_secrets(loader, vault_ids=vault_ids,
                                                     vault_password_files=list(context.CLIARGS['vault_password_files']),
                                                     ask_vault_pass=context.CLIARGS['ask_vault_pass'])
            if not vault_secrets:
                raise AnsibleOptionsError("A vault password is required to use Ansible's Vault")

        if action in ['encrypt', 'encrypt_string', 'create']:

            encrypt_vault_id = None
            # no --encrypt-vault-id context.CLIARGS['encrypt_vault_id'] for 'edit'
            if action not in ['edit']:
                encrypt_vault_id = context.CLIARGS['encrypt_vault_id'] or C.DEFAULT_VAULT_ENCRYPT_IDENTITY

            vault_secrets = None
            vault_secrets = \
                self.setup_vault_secrets(loader,
                                         vault_ids=vault_ids,
                                         vault_password_files=list(context.CLIARGS['vault_password_files']),
                                         ask_vault_pass=context.CLIARGS['ask_vault_pass'],
                                         create_new_password=True)

            if len(vault_secrets) > 1 and not encrypt_vault_id:
                raise AnsibleOptionsError("The vault-ids %s are available to encrypt. Specify the vault-id to encrypt with --encrypt-vault-id" %
                                          ','.join([x[0] for x in vault_secrets]))

            if not vault_secrets:
                raise AnsibleOptionsError("A vault password is required to use Ansible's Vault")

            encrypt_secret = match_encrypt_secret(vault_secrets,
                                                  encrypt_vault_id=encrypt_vault_id)

            # only one secret for encrypt for now, use the first vault_id and use its first secret
            # TODO: exception if more than one?
            self.encrypt_vault_id = encrypt_secret[0]
            self.encrypt_secret = encrypt_secret[1]

        if action in ['rekey']:
            encrypt_vault_id = context.CLIARGS['encrypt_vault_id'] or C.DEFAULT_VAULT_ENCRYPT_IDENTITY
            # print('encrypt_vault_id: %s' % encrypt_vault_id)
            # print('default_encrypt_vault_id: %s' % default_encrypt_vault_id)

            # new_vault_ids should only ever be one item, from
            # load the default vault ids if we are using encrypt-vault-id
            new_vault_ids = []
            if encrypt_vault_id:
                new_vault_ids = default_vault_ids
            if context.CLIARGS['new_vault_id']:
                new_vault_ids.append(context.CLIARGS['new_vault_id'])

            new_vault_password_files = []
            if context.CLIARGS['new_vault_password_file']:
                new_vault_password_files.append(context.CLIARGS['new_vault_password_file'])

            new_vault_secrets = \
                self.setup_vault_secrets(loader,
                                         vault_ids=new_vault_ids,
                                         vault_password_files=new_vault_password_files,
                                         ask_vault_pass=context.CLIARGS['ask_vault_pass'],
                                         initialize_context=False,
                                         create_new_password=True)

            if not new_vault_secrets:
                raise AnsibleOptionsError("A new vault password is required to use Ansible's Vault rekey")

            # There is only one new_vault_id currently and one new_vault_secret, or we
            # use the id specified in --encrypt-vault-id
            new_encrypt_secret = match_encrypt_secret(new_vault_secrets,
                                                      encrypt_vault_id=encrypt_vault_id)

            self.new_encrypt_vault_id = new_encrypt_secret[0]
            self.new_encrypt_secret = new_encrypt_secret[1]

        loader.set_vault_secrets(vault_secrets)

        # FIXME: do we need to create VaultEditor here? its not reused
        vault = VaultLib(vault_secrets)
        self.editor = VaultEditor(vault)

        context.CLIARGS['func']()

        # and restore umask
        os.umask(old_umask)
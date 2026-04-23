def __init__(self, module: AnsibleModule) -> None:
        # If the key is a url, we need to check if it's present to be idempotent,
        # to do that, we need to check the keyid, which we can get from the armor.
        keyfile = None
        should_cleanup_keyfile = False
        self.module = module
        self.rpm = self.module.get_bin_path('rpm', True)
        self.rpmkeys = self.module.get_bin_path('rpmkeys', True)
        state = module.params['state']
        key = module.params['key']
        fingerprint = module.params['fingerprint']
        fingerprints = set()

        if fingerprint:
            if not isinstance(fingerprint, list):
                fingerprint = [fingerprint]
            fingerprints = set(f.replace(' ', '').upper() for f in fingerprint)

        self.librpm = LibRPM()

        if '://' in key:
            keyfile = self.fetch_key(key)
            keyid = self.getkeyid(keyfile)
            should_cleanup_keyfile = True
        elif self.is_keyid(key):
            keyid = key
        elif os.path.isfile(key):
            keyfile = key
            keyid = self.getkeyid(keyfile)
        else:
            self.module.fail_json(msg="Not a valid key %s" % key)
        keyid = self.normalize_keyid(keyid)

        self.installed_keys = self.get_installed_keys()

        if state == 'present':
            if self.is_key_imported(keyid):
                module.exit_json(changed=False)
            else:
                if not keyfile:
                    self.module.fail_json(msg="When importing a key, a valid file must be given")
                if fingerprints:
                    keyfile_fingerprints = self.getfingerprints(keyfile)
                    if not fingerprints.issubset(keyfile_fingerprints):
                        self.module.fail_json(
                            msg=("The specified fingerprint, '%s', "
                                 "does not match any key fingerprints in '%s'") % (fingerprints, keyfile_fingerprints)
                        )
                self.import_key(keyfile)
                if should_cleanup_keyfile:
                    self.module.cleanup(keyfile)
                module.exit_json(changed=True)
        else:
            if self.is_key_imported(keyid):
                self.drop_key(keyid)
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)
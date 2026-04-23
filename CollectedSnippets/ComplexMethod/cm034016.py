def __init__(self, module):

        self.module = module

        self.allow_downgrade = self.module.params['allow_downgrade']
        self.allowerasing = self.module.params['allowerasing']
        self.autoremove = self.module.params['autoremove']
        self.best = self.module.params['best']
        self.bugfix = self.module.params['bugfix']
        self.cacheonly = self.module.params['cacheonly']
        self.conf_file = self.module.params['conf_file']
        self.disable_excludes = self.module.params['disable_excludes']
        self.disable_gpg_check = self.module.params['disable_gpg_check']
        self.disable_plugin = self.module.params['disable_plugin']
        self.disablerepo = self.module.params.get('disablerepo', [])
        self.download_only = self.module.params['download_only']
        self.download_dir = self.module.params['download_dir']
        self.enable_plugin = self.module.params['enable_plugin']
        self.enablerepo = self.module.params.get('enablerepo', [])
        self.exclude = self.module.params['exclude']
        self.installroot = self.module.params['installroot']
        self.install_weak_deps = self.module.params['install_weak_deps']
        self.list = self.module.params['list']
        self.names = [p.strip() for p in self.module.params['name']]
        self.nobest = self.module.params['nobest']
        self.releasever = self.module.params['releasever']
        self.security = self.module.params['security']
        self.skip_broken = self.module.params['skip_broken']
        self.state = self.module.params['state']
        self.update_only = self.module.params['update_only']
        self.update_cache = self.module.params['update_cache']
        self.validate_certs = self.module.params['validate_certs']
        self.sslverify = self.module.params['sslverify']
        self.lock_timeout = self.module.params['lock_timeout']

        # It's possible someone passed a comma separated string since it used
        # to be a string type, so we should handle that
        self.names = self.listify_comma_sep_strings_in_list(self.names)
        self.disablerepo = self.listify_comma_sep_strings_in_list(self.disablerepo)
        self.enablerepo = self.listify_comma_sep_strings_in_list(self.enablerepo)
        self.exclude = self.listify_comma_sep_strings_in_list(self.exclude)

        # Fail if someone passed a space separated string
        # https://github.com/ansible/ansible/issues/46301
        for name in self.names:
            if ' ' in name and not any(spec in name for spec in ['@', '>', '<', '=']):
                module.fail_json(
                    msg='It appears that a space separated string of packages was passed in '
                        'as an argument. To operate on several packages, pass a comma separated '
                        'string of packages or a list of packages.'
                )

        # Sanity checking for autoremove
        if self.state is None:
            if self.autoremove:
                self.state = "absent"
            else:
                self.state = "present"

        if self.autoremove and (self.state != "absent"):
            self.module.fail_json(
                msg="Autoremove should be used alone or with state=absent",
                results=[],
            )
def add_source(self, line, comment='', file=None):
        if line.startswith('ppa:'):
            source, ppa_owner, ppa_name = self._expand_ppa(line)

            if source in self.repos_urls:
                # repository already exists
                return

            info = self._get_ppa_info(ppa_owner, ppa_name)

            # add gpg sig if needed
            if not self._key_already_exists(info['signing_key_fingerprint']):

                # TODO: report file that would have been added if not check_mode
                keyfile = ''
                if not self.module.check_mode:
                    if self.apt_key_bin:
                        command = [self.apt_key_bin, 'adv', '--recv-keys', '--no-tty', '--keyserver', 'hkp://keyserver.ubuntu.com:80',
                                   info['signing_key_fingerprint']]
                    else:
                        # use first available key dir, in order of preference
                        for keydir in APT_KEY_DIRS:
                            if os.path.exists(keydir):
                                break
                        else:
                            self.module.fail_json("Unable to find any existing apt gpgp repo directories, tried the following: %s" % ', '.join(APT_KEY_DIRS))

                        keyfile = '%s/%s-%s-%s.gpg' % (keydir, os.path.basename(source).replace(' ', '-'), ppa_owner, ppa_name)
                        command = [self.gpg_bin, '--no-tty', '--keyserver', 'hkp://keyserver.ubuntu.com:80', '--export', info['signing_key_fingerprint']]

                    rc, stdout, stderr = self.module.run_command(command, check_rc=True, encoding=None)
                    if keyfile:
                        # using gpg we must write keyfile ourselves
                        if len(stdout) == 0:
                            self.module.fail_json(msg='Unable to get required signing key', rc=rc, stderr=stderr, command=command)
                        try:
                            with open(keyfile, 'wb') as f:
                                f.write(stdout)
                            self.module.log('Added repo key "%s" for apt to file "%s"' % (info['signing_key_fingerprint'], keyfile))
                        except OSError as ex:
                            self.module.fail_json(msg='Unable to add required signing key.', rc=rc, stderr=stderr, error=str(ex), exception=ex)

            # apt source file
            file = file or self._suggest_filename('%s_%s' % (line, self.codename))
        else:
            source = self._parse(line, raise_if_invalid_or_disabled=True)[2]
            file = file or self._suggest_filename(source)

        self._add_valid_source(source, comment, file)
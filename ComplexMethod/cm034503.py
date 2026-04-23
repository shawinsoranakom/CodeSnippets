def _gpg_key_exists(self, key_fingerprint):

        found = False
        keyfiles = ['/etc/apt/trusted.gpg']  # main gpg repo for apt
        for other_dir in APT_KEY_DIRS:
            # add other known sources of gpg sigs for apt, skip hidden files
            keyfiles.extend([os.path.join(other_dir, x) for x in os.listdir(other_dir) if not x.startswith('.')])

        for key_file in keyfiles:

            if os.path.exists(key_file):
                try:
                    rc, out, err = self.module.run_command([self.gpg_bin, '--list-packets', key_file])
                except OSError as ex:
                    self.module.debug(f"Could check key against file {key_file!r}: {ex}")
                    continue

                if key_fingerprint in out:
                    found = True
                    break

        return found
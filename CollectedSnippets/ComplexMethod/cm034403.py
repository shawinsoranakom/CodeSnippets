def create_homedir(self, path):
        if not os.path.exists(path):
            if self.skeleton is not None:
                skeleton = self.skeleton
            else:
                skeleton = '/etc/skel'

            if os.path.exists(skeleton) and skeleton != os.devnull:
                try:
                    shutil.copytree(skeleton, path, symlinks=True)
                except OSError as e:
                    self.module.exit_json(failed=True, msg="%s" % to_native(e))
            else:
                try:
                    os.makedirs(path)
                except OSError as e:
                    self.module.exit_json(failed=True, msg="%s" % to_native(e))
            # get umask from /etc/login.defs and set correct home mode
            if os.path.exists(self.LOGIN_DEFS):
                # fallback if neither HOME_MODE nor UMASK are set;
                # follow behaviour of useradd initializing UMASK = 022
                mode = 0o755
                with open(self.LOGIN_DEFS, 'r') as fh:
                    for line in fh:
                        # HOME_MODE has higher precedence as UMASK
                        match = re.match(r'^HOME_MODE\s+(\d+)$', line)
                        if match:
                            mode = int(match.group(1), 8)
                            break  # higher precedence
                        match = re.match(r'^UMASK\s+(\d+)$', line)
                        if match:
                            umask = int(match.group(1), 8)
                            mode = 0o777 & ~umask
                try:
                    os.chmod(path, mode)
                except OSError as e:
                    self.module.exit_json(failed=True, msg=to_native(e))
def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        becomecmd = self.get_option('become_exe') or self.name

        flags = self.get_option('become_flags') or ''
        prompt = ''
        if self.get_option('become_pass'):
            self.prompt = '[sudo via ansible, key=%s] password:' % self._id
            if flags:  # this could be simplified, but kept as is for now for backwards string matching
                reflag = []
                for flag in shlex.split(flags):
                    if flag in ('-n', '--non-interactive'):
                        continue
                    elif not flag.startswith('--'):
                        # handle -XnxxX flags only
                        flag = re.sub(r'^(-\w*)n(\w*.*)', r'\1\2', flag)
                    reflag.append(flag)
                flags = shlex.join(reflag)

            prompt = '-p "%s"' % (self.prompt)

        user = self.get_option('become_user') or ''
        if user:
            user = '-u %s' % (user)

        if chdir := self.get_option('sudo_chdir'):
            try:
                becomecmd = f'{shell.CD} {shlex.quote(chdir)} {shell._SHELL_AND} {becomecmd}'
            except AttributeError as ex:
                raise AnsibleError(f'The {shell._load_name!r} shell plugin does not support sudo chdir. It is missing the {ex.name!r} attribute.')

        return ' '.join([becomecmd, flags, prompt, user, self._build_success_command(cmd, shell)])
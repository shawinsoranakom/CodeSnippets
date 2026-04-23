def unarchive(self):
        cmd = [self.cmd_path, '--extract', '-C', self.b_dest]
        if self.zipflag:
            cmd.append(self.zipflag)
        if self.opts:
            cmd.extend(['--show-transformed-names'] + self.opts)
        if self.file_args['owner']:
            cmd.append('--owner=' + quote(self.file_args['owner']))
        if self.file_args['group']:
            cmd.append('--group=' + quote(self.file_args['group']))
        if self.module.params['keep_newer']:
            cmd.append('--keep-newer-files')
        if self.excludes:
            cmd.extend(['--exclude=' + f for f in self.excludes])
        cmd.extend(['-f', self.src])
        if self.include_files:
            cmd.extend(self.include_files)
        locale = get_best_parsable_locale(self.module)
        rc, out, err = self.module.run_command(cmd, cwd=self.b_dest, environ_update=dict(LANG=locale, LC_ALL=locale, LC_MESSAGES=locale, LANGUAGE=locale))
        return dict(cmd=cmd, rc=rc, out=out, err=err)
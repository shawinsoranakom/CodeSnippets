def create_user(self):
        cmd = [self.module.get_bin_path('adduser', True)]

        cmd.append('-D')

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg=f'Group {self.group} does not exist')

            cmd.append('-G')
            cmd.append(self.group)

        if self.comment is not None:
            cmd.append('-g')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-h')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if not self.create_home:
            cmd.append('-H')

        if self.skeleton is not None:
            cmd.append('-k')
            cmd.append(self.skeleton)

        if self.umask is not None:
            cmd.append('-K')
            cmd.append('UMASK=' + self.umask)

        if self.system:
            cmd.append('-S')

        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)

        rc, out, err = self.execute_command(cmd)

        if rc is not None and rc != 0:
            self.module.fail_json(name=self.name, msg=err, rc=rc)

        cmd = [self.module.get_bin_path('chpasswd', True)]
        cmd.append('--encrypted')
        data = f'{self.name}:{self._build_password_string()}'
        rc, out, err = self.execute_command(cmd, data=data)

        if rc is not None and rc != 0:
            self.module.fail_json(name=self.name, msg=err, rc=rc)

        # Add to additional groups
        if self.groups:
            groups = self.get_groups_set() or set()
            add_cmd_bin = self.module.get_bin_path('adduser', True)
            for group in groups:
                cmd = [add_cmd_bin, self.name, group]
                rc, out, err = self.execute_command(cmd)
                if rc is not None and rc != 0:
                    self.module.fail_json(name=self.name, msg=err, rc=rc)

        return rc, out, err
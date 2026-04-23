def create_user_useradd(self, command_name='useradd'):
        cmd = [self.module.get_bin_path(command_name, True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None and len(self.groups):
            groups = self.get_groups_set()
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.create_home:
            cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)
        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)
        (rc, out, err) = self.execute_command(cmd)

        # set password with chpasswd
        if self.password is not None:
            cmd = []
            cmd.append(self.module.get_bin_path('chpasswd', True))
            cmd.append('-e')
            cmd.append('-c')
            self.execute_command(cmd, data="%s:%s" % (self.name, self.password))

        return (rc, out, err)
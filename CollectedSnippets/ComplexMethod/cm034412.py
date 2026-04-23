def create_user(self):
        cmd = [self.module.get_bin_path('useradd', True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None:
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

        if self.profile is not None:
            cmd.append('-P')
            cmd.append(self.profile)

        if self.authorization is not None:
            cmd.append('-A')
            cmd.append(self.authorization)

        if self.role is not None:
            cmd.append('-R')
            cmd.append(self.role)

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
        if rc is not None and rc != 0:
            self.module.fail_json(name=self.name, msg=err, rc=rc)

        if not self.module.check_mode:
            # we have to set the password by editing the /etc/shadow file
            if self.password is not None:
                self.backup_shadow()
                minweeks, maxweeks, warnweeks = self.get_password_defaults()
                try:
                    lines = []
                    with open(self.SHADOWFILE, 'rb') as f:
                        for line in f:
                            line = to_native(line, errors='surrogate_or_strict')
                            fields = line.strip().split(':')
                            if not fields[0] == self.name:
                                lines.append(line)
                                continue
                            fields[1] = self.password
                            fields[2] = str(int(time.time() // 86400))
                            if minweeks:
                                try:
                                    fields[3] = str(int(minweeks) * 7)
                                except ValueError:
                                    # mirror solaris, which allows for any value in this field, and ignores anything that is not an int.
                                    pass
                            if maxweeks:
                                try:
                                    fields[4] = str(int(maxweeks) * 7)
                                except ValueError:
                                    # mirror solaris, which allows for any value in this field, and ignores anything that is not an int.
                                    pass
                            if warnweeks:
                                try:
                                    fields[5] = str(int(warnweeks) * 7)
                                except ValueError:
                                    # mirror solaris, which allows for any value in this field, and ignores anything that is not an int.
                                    pass
                            line = ':'.join(fields)
                            lines.append('%s\n' % line)
                    with open(self.SHADOWFILE, 'w+') as f:
                        f.writelines(lines)
                except Exception as err:
                    self.module.fail_json(msg="failed to update users password: %s" % to_native(err))

        return (rc, out, err)
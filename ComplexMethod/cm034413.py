def modify_user_usermod(self):
        cmd = [self.module.get_bin_path('usermod', True)]
        cmd_len = len(cmd)
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups = self.get_groups_set(names_only=True)
            group_diff = set(current_groups).symmetric_difference(groups)
            groups_need_mod = False

            if group_diff:
                if self.append:
                    for g in groups:
                        if g in group_diff:
                            groups_need_mod = True
                            break
                else:
                    groups_need_mod = True

            if groups_need_mod:
                cmd.append('-G')
                new_groups = groups
                if self.append:
                    new_groups.update(current_groups)
                cmd.append(','.join(new_groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            if self.move_home:
                cmd.append('-m')
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.profile is not None and info[7] != self.profile:
            cmd.append('-P')
            cmd.append(self.profile)

        if self.authorization is not None and info[8] != self.authorization:
            cmd.append('-A')
            cmd.append(self.authorization)

        if self.role is not None and info[9] != self.role:
            cmd.append('-R')
            cmd.append(self.role)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        # modify the user if cmd will do anything
        if cmd_len != len(cmd):
            cmd.append(self.name)
            (rc, out, err) = self.execute_command(cmd)
            if rc is not None and rc != 0:
                self.module.fail_json(name=self.name, msg=err, rc=rc)
        else:
            (rc, out, err) = (None, '', '')

        # we have to set the password by editing the /etc/shadow file
        if self.update_password == 'always' and self.password is not None and info[1] != self.password:
            self.backup_shadow()
            (rc, out, err) = (0, '', '')
            if not self.module.check_mode:
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
                                fields[3] = str(int(minweeks) * 7)
                            if maxweeks:
                                fields[4] = str(int(maxweeks) * 7)
                            if warnweeks:
                                fields[5] = str(int(warnweeks) * 7)
                            line = ':'.join(fields)
                            lines.append('%s\n' % line)
                    with open(self.SHADOWFILE, 'w+') as f:
                        f.writelines(lines)
                    rc = 0
                except Exception as err:
                    self.module.fail_json(msg="failed to update users password: %s" % to_native(err))

        return (rc, out, err)
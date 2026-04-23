def modify_user(self):
        cmd = [self.module.get_bin_path('usermod', True)]
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
            groups_need_mod = False
            groups = []

            if self.groups == '':
                if current_groups and not self.append:
                    groups_need_mod = True
            else:
                groups = self.get_groups_set(names_only=True)
                group_diff = set(current_groups).symmetric_difference(groups)

                if group_diff:
                    if self.append:
                        for g in groups:
                            if g in group_diff:
                                groups = set(current_groups).union(groups)
                                groups_need_mod = True
                                break
                    else:
                        groups_need_mod = True

            if groups_need_mod:
                if len(groups) > 16:
                    self.module.fail_json(msg="Too many groups (%d) NetBSD allows for 16 max." % len(groups))
                cmd.append('-G')
                cmd.append(','.join(groups))

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

        if self.login_class is not None:
            cmd.append('-L')
            cmd.append(self.login_class)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        if self.update_password == 'always' and self.password is not None and info[1] != self.password:
            cmd.append('-p')
            cmd.append(self.password)

        if self.password_lock and not info[1].startswith('*LOCKED*'):
            cmd.append('-C yes')
        elif self.password_lock is False and info[1].startswith('*LOCKED*'):
            cmd.append('-C no')

        # skip if no changes to be made
        if len(cmd) == 1:
            return (None, '', '')

        cmd.append(self.name)
        return self.execute_command(cmd)
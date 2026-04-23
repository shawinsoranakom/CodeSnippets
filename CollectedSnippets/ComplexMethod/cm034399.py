def modify_user_usermod(self):

        if self.local:
            command_name = 'lusermod'
            lgroupmod_cmd = self.module.get_bin_path('lgroupmod', True)
            lgroupmod_add = set()
            lgroupmod_del = set()
            lchage_cmd = self.module.get_bin_path('lchage', True)
            lexpires = None
        else:
            command_name = 'usermod'

        cmd = [self.module.get_bin_path(command_name, True)]
        info = self.user_info()
        has_append = self._check_usermod_append()

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
                cmd.append(ginfo[2])

        if self.groups is not None:
            # get a list of all groups for the user, including the primary
            current_groups = self.user_group_membership(exclude_primary=False)
            groups_need_mod = False
            groups = []

            if self.groups == '':
                if current_groups and not self.append:
                    groups_need_mod = True
            else:
                groups = self.get_groups_set(remove_existing=False, names_only=True)
                group_diff = set(current_groups).symmetric_difference(groups)

                if group_diff:
                    if self.append:
                        for g in groups:
                            if g in group_diff:
                                if has_append:
                                    cmd.append('-a')
                                groups_need_mod = True
                                break
                    else:
                        groups_need_mod = True

            if groups_need_mod:
                if self.local:
                    if self.append:
                        lgroupmod_add = set(groups).difference(current_groups)
                        lgroupmod_del = set()
                    else:
                        lgroupmod_add = set(groups).difference(current_groups)
                        lgroupmod_del = set(current_groups).difference(groups)
                else:
                    if self.append and not has_append:
                        cmd.append('-A')
                        cmd.append(','.join(group_diff))
                    else:
                        cmd.append('-G')
                        cmd.append(','.join(groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            cmd.append('-d')
            cmd.append(self.home)
            if self.move_home:
                cmd.append('-m')

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.expires is not None:

            current_expires = self.user_password()[1] or '0'
            current_expires = int(current_expires)

            if self.expires < time.gmtime(0):
                if current_expires >= 0:
                    if self.local:
                        lexpires = -1
                    else:
                        cmd.append('-e')
                        cmd.append('')
            else:
                # Convert days since Epoch to seconds since Epoch as struct_time
                current_expire_date = time.gmtime(current_expires * 86400)

                # Current expires is negative or we compare year, month, and day only
                if current_expires < 0 or current_expire_date[:3] != self.expires[:3]:
                    if self.local:
                        # Convert seconds since Epoch to days since Epoch
                        lexpires = int(math.floor(self.module.params['expires'])) // 86400
                    else:
                        cmd.append('-e')
                        cmd.append(time.strftime(self.DATE_FORMAT, self.expires))

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        # Lock if no password or unlocked, unlock only if locked
        if self.password_lock and not info[1].startswith('!'):
            cmd.append('-L')
        elif self.password_lock is False and info[1].startswith('!'):
            # usermod will refuse to unlock a user with no password, module shows 'changed' regardless
            cmd.append('-U')

        if self.update_password == 'always' and self.password is not None and info[1].lstrip('!') != self.password.lstrip('!'):
            # Remove options that are mutually exclusive with -p
            cmd = [c for c in cmd if c not in ['-U', '-L']]
            cmd.append('-p')
            if self.password_lock:
                # Lock the account and set the hash in a single command
                cmd.append('!%s' % self.password)
            else:
                cmd.append(self.password)

        (rc, out, err) = (None, '', '')

        # skip if no usermod changes to be made
        if len(cmd) > 1:
            cmd.append(self.name)
            (rc, out, err) = self.execute_command(cmd)

        if not self.local or not (rc is None or rc == 0):
            return (rc, out, err)

        if lexpires is not None:
            (rc, _out, _err) = self.execute_command([lchage_cmd, '-E', to_native(lexpires), self.name])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)

        if len(lgroupmod_add) == 0 and len(lgroupmod_del) == 0:
            return (rc, out, err)

        for add_group in lgroupmod_add:
            (rc, _out, _err) = self.execute_command([lgroupmod_cmd, '-M', self.name, add_group])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)

        for del_group in lgroupmod_del:
            (rc, _out, _err) = self.execute_command([lgroupmod_cmd, '-m', self.name, del_group])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)
        return (rc, out, err)
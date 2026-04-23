def create_user_useradd(self):

        if self.local:
            command_name = 'luseradd'
            lgroupmod_cmd = self.module.get_bin_path('lgroupmod', True)
            lchage_cmd = self.module.get_bin_path('lchage', True)
        else:
            command_name = 'useradd'

        cmd = [self.module.get_bin_path(command_name, True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.seuser is not None and self.module.selinux_enabled():
            cmd.append('-Z')
            cmd.append(self.seuser)
        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)
        elif self.group_exists(self.name):
            # use the -N option (no user group) if a group already
            # exists with the same name as the user to prevent
            # errors from useradd trying to create a group when
            # USERGROUPS_ENAB is set in /etc/login.defs.
            if self.local:
                # luseradd uses -n instead of -N
                cmd.append('-n')
            else:
                if os.path.exists('/etc/redhat-release'):
                    dist = distro.version()
                    major_release = int(dist.split('.')[0])
                    if major_release <= 5:
                        cmd.append('-n')
                    else:
                        cmd.append('-N')
                elif os.path.exists('/etc/SuSE-release'):
                    # -N did not exist in useradd before SLE 11 and did not
                    # automatically create a group
                    dist = distro.version()
                    major_release = int(dist.split('.')[0])
                    if major_release >= 12:
                        cmd.append('-N')
                else:
                    cmd.append('-N')

        if self.groups is not None and len(self.groups):
            groups = self.get_groups_set()
            if not self.local:
                cmd.append('-G')
                cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            # If the specified path to the user home contains parent directories that
            # do not exist and create_home is True first create the parent directory
            # since useradd cannot create it.
            if self.create_home:
                parent = os.path.dirname(self.home)
                if not os.path.isdir(parent):
                    self.create_homedir(self.home)
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.expires is not None and not self.local:
            cmd.append('-e')
            if self.expires < time.gmtime(0):
                cmd.append('')
            else:
                cmd.append(time.strftime(self.DATE_FORMAT, self.expires))

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(int(self.inactive))

        if self.password is not None:
            cmd.append('-p')
            if self.password_lock:
                cmd.append('!%s' % self.password)
            else:
                cmd.append(self.password)

        if self.create_home:
            if not self.local:
                cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)
        else:
            cmd.append('-M')

        if self.system:
            cmd.append('-r')

        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)
        (rc, out, err) = self.execute_command(cmd)
        if not self.local or rc != 0:
            return (rc, out, err)

        if self.expires is not None:
            if self.expires < time.gmtime(0):
                lexpires = -1
            else:
                # Convert seconds since Epoch to days since Epoch
                lexpires = int(math.floor(self.module.params['expires'])) // 86400
            (rc, _out, _err) = self.execute_command([lchage_cmd, '-E', to_native(lexpires), self.name])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)

        if self.groups is None or len(self.groups) == 0:
            return (rc, out, err)

        for add_group in groups:
            (rc, _out, _err) = self.execute_command([lgroupmod_cmd, '-M', self.name, add_group])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)
        return (rc, out, err)
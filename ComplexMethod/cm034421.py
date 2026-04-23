def create_user(self):
        cmd = ['/usr/sam/lbin/useradd.sam']

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

        if self.password is not None:
            cmd.append('-p')
            cmd.append(self.password)

        if self.create_home:
            cmd.append('-m')
        else:
            cmd.append('-M')

        if self.system:
            cmd.append('-r')

        cmd.append(self.name)
        return self.execute_command(cmd)
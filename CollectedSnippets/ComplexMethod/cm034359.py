def group_add(self, **kwargs):
        if self.local:
            command_name = 'lgroupadd'
            self._local_check_gid_exists()
        else:
            command_name = 'groupadd'
        cmd = [self.module.get_bin_path(command_name, True)]
        for key in kwargs:
            if key == 'gid' and kwargs[key] is not None:
                cmd.append('-g')
                cmd.append(str(kwargs[key]))
                if self.non_unique:
                    cmd.append('-o')
            elif key == 'system' and kwargs[key] is True:
                cmd.append('-r')
        if self.gid_min is not None:
            cmd.append('-K')
            cmd.append('GID_MIN=' + str(self.gid_min))
        if self.gid_max is not None:
            cmd.append('-K')
            cmd.append('GID_MAX=' + str(self.gid_max))
        cmd.append(self.name)
        return self.execute_command(cmd)
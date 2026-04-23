def group_mod(self, **kwargs):
        if self.local:
            command_name = 'lgroupmod'
            self._local_check_gid_exists()
        else:
            command_name = 'groupmod'
        cmd = [self.module.get_bin_path(command_name, True)]
        info = self.group_info()
        for key in kwargs:
            if key == 'gid':
                if kwargs[key] is not None and info[2] != int(kwargs[key]):
                    cmd.append('-g')
                    cmd.append(str(kwargs[key]))
                    if self.non_unique:
                        cmd.append('-o')
        if len(cmd) == 1:
            return (None, '', '')
        if self.module.check_mode:
            return (0, '', '')
        cmd.append(self.name)
        return self.execute_command(cmd)
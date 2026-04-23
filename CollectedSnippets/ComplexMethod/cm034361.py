def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('mkgroup', True)]
        for key in kwargs:
            if key == 'gid' and kwargs[key] is not None:
                cmd.append('id=' + str(kwargs[key]))
            elif key == 'system' and kwargs[key] is True:
                cmd.append('-a')
        if self.gid_min is not None:
            cmd.append('-K')
            cmd.append('GID_MIN=' + str(self.gid_min))
        if self.gid_max is not None:
            cmd.append('-K')
            cmd.append('GID_MAX=' + str(self.gid_max))
        cmd.append(self.name)
        return self.execute_command(cmd)
def _handle_lock(self):
        info = self.user_info()
        if self.password_lock and not info[1].startswith('*LOCKED*'):
            cmd = [
                self.module.get_bin_path('pw', True),
                'lock',
                self.name
            ]
            if self.uid is not None and info[2] != int(self.uid):
                cmd.append('-u')
                cmd.append(self.uid)
            return self.execute_command(cmd)
        elif self.password_lock is False and info[1].startswith('*LOCKED*'):
            cmd = [
                self.module.get_bin_path('pw', True),
                'unlock',
                self.name
            ]
            if self.uid is not None and info[2] != int(self.uid):
                cmd.append('-u')
                cmd.append(self.uid)
            return self.execute_command(cmd)

        return (None, '', '')
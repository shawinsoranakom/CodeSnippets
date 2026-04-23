def set_password_expire(self):
        min_needs_change = self.password_expire_min is not None
        max_needs_change = self.password_expire_max is not None
        warn_needs_change = self.password_expire_warn is not None

        if HAVE_SPWD:
            try:
                shadow_info = getspnam(to_bytes(self.name))
            except ValueError:
                return None, '', ''

            min_needs_change &= self.password_expire_min != shadow_info.sp_min
            max_needs_change &= self.password_expire_max != shadow_info.sp_max
            warn_needs_change &= self.password_expire_warn != shadow_info.sp_warn

        if not (min_needs_change or max_needs_change or warn_needs_change):
            return (None, '', '')  # target state already reached

        command_name = 'chage'
        cmd = [self.module.get_bin_path(command_name, True)]
        if min_needs_change:
            cmd.extend(["-m", self.password_expire_min])
        if max_needs_change:
            cmd.extend(["-M", self.password_expire_max])
        if warn_needs_change:
            cmd.extend(["-W", self.password_expire_warn])
        cmd.append(self.name)

        return self.execute_command(cmd)
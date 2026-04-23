def get_lowest_available_system_gid(self):
        # check for lowest available system gid (< 500)
        try:
            cmd = [self.module.get_bin_path('dscl', True)]
            cmd += ['/Local/Default', '-list', '/Groups', 'PrimaryGroupID']
            (rc, out, err) = self.execute_command(cmd)
            lines = out.splitlines()
            highest = 0
            for group_info in lines:
                parts = group_info.split(' ')
                if len(parts) > 1:
                    gid = int(parts[-1])
                    if gid > highest and gid < 500:
                        highest = gid
            if highest == 0 or highest == 499:
                return False
            return (highest + 1)
        except Exception:
            return False
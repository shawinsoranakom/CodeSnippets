def _get_next_uid(self, system=None):
        """
        Return the next available uid. If system=True, then
        uid should be below of 500, if possible.
        """
        cmd = self._get_dscl()
        cmd += ['-list', '/Users', 'UniqueID']
        (rc, out, err) = self.execute_command(cmd, obey_checkmode=False)
        if rc != 0:
            self.module.fail_json(
                msg="Unable to get the next available uid",
                rc=rc,
                out=out,
                err=err
            )

        max_uid = 0
        max_system_uid = 0
        for line in out.splitlines():
            current_uid = int(line.split(' ')[-1])
            if max_uid < current_uid:
                max_uid = current_uid
            if max_system_uid < current_uid and current_uid < 500:
                max_system_uid = current_uid

        if system and (0 < max_system_uid < 499):
            return max_system_uid + 1
        return max_uid + 1
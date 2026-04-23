def _update_system_user(self):
        """Hide or show user on login window according SELF.SYSTEM.

        Returns 0 if a change has been made, None otherwise."""

        plist_file = '/Library/Preferences/com.apple.loginwindow.plist'

        # http://support.apple.com/kb/HT5017?viewlocale=en_US
        cmd = ['defaults', 'read', plist_file, 'HiddenUsersList']
        (rc, out, err) = self.execute_command(cmd, obey_checkmode=False)
        # returned value is
        # (
        #   "_userA",
        #   "_UserB",
        #   userc
        # )
        hidden_users = []
        for x in out.splitlines()[1:-1]:
            try:
                x = x.split('"')[1]
            except IndexError:
                x = x.strip()
            hidden_users.append(x)

        if self.system:
            if self.name not in hidden_users:
                cmd = ['defaults', 'write', plist_file, 'HiddenUsersList', '-array-add', self.name]
                (rc, out, err) = self.execute_command(cmd)
                if rc != 0:
                    self.module.fail_json(msg='Cannot user "%s" to hidden user list.' % self.name, err=err, out=out, rc=rc)
                return 0
        else:
            if self.name in hidden_users:
                del (hidden_users[hidden_users.index(self.name)])

                cmd = ['defaults', 'write', plist_file, 'HiddenUsersList', '-array'] + hidden_users
                (rc, out, err) = self.execute_command(cmd)
                if rc != 0:
                    self.module.fail_json(msg='Cannot remove user "%s" from hidden user list.' % self.name, err=err, out=out, rc=rc)
                return 0
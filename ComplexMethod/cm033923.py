def _remote_expand_user(self, path, sudoable=True, pathsep=None):
        """ takes a remote path and performs tilde/$HOME expansion on the remote host """

        # We only expand ~/path and ~username/path
        if not path.startswith('~'):
            return path

        # Per Jborean, we don't have to worry about Windows as we don't have a notion of user's home
        # dir there.
        split_path = path.split(os.path.sep, 1)
        expand_path = split_path[0]

        if expand_path == '~':
            # Network connection plugins (network_cli, netconf, etc.) execute on the controller, rather than the remote host.
            # As such, we want to avoid using remote_user for paths  as remote_user may not line up with the local user
            # This is a hack and should be solved by more intelligent handling of remote_tmp in 2.7
            become_user = self.get_become_option('become_user')
            if getattr(self._connection, '_remote_is_local', False):
                pass
            elif sudoable and self._connection.become and become_user:
                expand_path = '~%s' % become_user
            else:
                # use remote user instead, if none set default to current user
                expand_path = '~%s' % (self._get_remote_user() or '')

        # use shell to construct appropriate command and execute
        cmd = None
        in_data = None
        if self._connection.is_pipelining_enabled(wrap_async=False):
            cmd_details = self._connection._shell._expand_user2(expand_path)
            cmd = cmd_details.command
            in_data = cmd_details.input_data
        else:
            cmd = self._connection._shell.expand_user(expand_path)
        data = self._low_level_execute_command(cmd, in_data=in_data, sudoable=False)

        try:
            initial_fragment = data['stdout'].strip().splitlines()[-1]
        except IndexError:
            initial_fragment = None

        if not initial_fragment:
            # Something went wrong trying to expand the path remotely. Try using pwd, if not, return
            # the original string
            cmd = self._connection._shell.pwd()
            pwd = self._low_level_execute_command(cmd, sudoable=False).get('stdout', '').strip()
            if pwd:
                expanded = pwd
            else:
                expanded = path

        elif len(split_path) > 1:
            expanded = self._connection._shell.join_path(initial_fragment, *split_path[1:])
        else:
            expanded = initial_fragment

        if '..' in os.path.dirname(expanded).split('/'):
            raise AnsibleError("'%s' returned an invalid relative home directory path containing '..'" % self._get_remote_addr({}))

        return expanded